import json
from django.core.management.base import BaseCommand

from ...models.scannerjobs.scanner_model import Scanner, ScanStatus
from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.pipeline.run_stage import _loglevels
from os2datascanner.engine2.pipeline.utilities import pika

import logging


logger = logging.getLogger(__name__)


def scan_tag(s):
    return messages.ScanTagFragment.from_json_object(json.loads(s))


def model_pk(model, constructor=int):
    def _pk(s):
        return model.objects.get(pk=constructor(s))
    return _pk


class Command(BaseCommand):
    """Interact with a running OS2datascanner pipeline by sending it a command
    message."""
    help = __doc__

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
                "--abort-scantag",
                type=scan_tag,
                metavar="SCAN_TAG",
                help="the tag of a running scan that should be stopped",
                default=None)
        group.add_argument(
                "--abort-scannerjob",
                type=model_pk(Scanner),
                metavar="PK",
                help="the primary key of a scanner job whose most recent scan"
                        " should be stopped",
                default=None)
        group.add_argument(
                "--abort-scanstatus",
                type=model_pk(ScanStatus),
                metavar="PK",
                help="the primary key of a ScanStatus object whose scan should be stopped",
                default=None)
        group.add_argument(
                "--log-level",
                choices=("critical", "error", "warn",
                         "warning", "info", "debug",),
                metavar="LEVEL",
                help="the new log level for pipeline components",
                default=None)

    def handle(self,
               abort_scantag, abort_scannerjob, abort_scanstatus, log_level,
               *args, **options):
        if abort_scannerjob:
            abort_scantag = messages.ScanTagFragment.from_json_object(
                    abort_scannerjob.statuses.last().scan_tag)
        elif abort_scanstatus:
            abort_scantag = messages.ScanTagFragment.from_json_object(
                    abort_scanstatus.scan_tag)

        msg = messages.CommandMessage(
                abort=abort_scantag,
                log_level=_loglevels.get(log_level) if log_level else None)
        logging.info(msg)

        with pika.PikaPipelineThread() as p:
            p.enqueue_message(
                    pika.ANON_QUEUE, msg.to_json_object(),
                    "broadcast", priority=10)
            p.enqueue_stop()
            p.run()
