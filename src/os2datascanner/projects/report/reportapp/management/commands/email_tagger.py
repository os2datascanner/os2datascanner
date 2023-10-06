import logging
import structlog
from django.conf import settings
from os2datascanner.utils import debug
from os2datascanner.utils.log_levels import log_levels
from django.core.management import BaseCommand
from os2datascanner.engine2.model.core import SourceManager
from os2datascanner.engine2.pipeline.utilities.pika import PikaPipelineThread


from prometheus_client import Summary, start_http_server

from ...models.documentreport import DocumentReport
from ...views.utilities.msgraph_utilities import get_mail_message_handle_from_document_report, \
    categorize_email_from_report

logger = structlog.get_logger(__name__)
SUMMARY = Summary("os2datascanner_email_tagger",
                  "Messages through os2ds_email_tags")


class EmailTaggerRunner(PikaPipelineThread):
    def __init__(self, source_manager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source_manager = source_manager
        start_http_server(9091)

    def handle_message(self, routing_key, body):
        with SUMMARY.time():
            logger.debug(
                "raw message received",
                routing_key=routing_key,
                body=body)
            if routing_key == "os2ds_email_tags":
                dr_pk, category_to_add = body
                try:
                    document_report = DocumentReport.objects.get(pk=dr_pk)
                    mail_handle = get_mail_message_handle_from_document_report(document_report)
                    mail_source = mail_handle.source
                    # We censor these when going through our pipeline, hence we need to set them
                    # again from settings.
                    mail_source.handle.source._client_id = settings.MSGRAPH_APP_ID
                    mail_source.handle.source._client_secret = settings.MSGRAPH_CLIENT_SECRET
                except DocumentReport.DoesNotExist:
                    logger.warning(f"Can't categorize email, document report not found: {dr_pk}")

                gc = self.source_manager.open(mail_source)
                categorize_email_from_report(document_report,
                                             category_to_add,
                                             gc)

                yield from []


class Command(BaseCommand):
    """Starts an email tagger process."""

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "--log",
            default="info",
            help="change the level at which log messages will be printed",
            choices=log_levels.keys())

    def handle(self, *args, log, **options):
        debug.register_debug_signal()

        # change formatting to include datestamp
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(format=fmt, datefmt='%Y-%m-%d %H:%M:%S')
        # set level for root logger
        logging.getLogger("os2datascanner").setLevel(log_levels[log])

        with SourceManager() as source_manager:
            EmailTaggerRunner(
                read=["os2ds_email_tags"],
                prefetch_count=8,
                source_manager=source_manager).run_consumer()
