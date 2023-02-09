import json
import argparse
from django.core.management.base import BaseCommand

from ...models.scannerjobs.scanner import Scanner, ScanStatus
from os2datascanner.utils.log_levels import log_levels
from os2datascanner.engine2.pipeline import messages
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
        group = parser.add_mutually_exclusive_group(required=False)
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

        parser.add_argument(
                "--log-level",
                choices=log_levels.keys(),
                metavar="LEVEL",
                help="the new log level for pipeline components",
                default=None)
        parser.add_argument(
                "--profile",
                action=argparse.BooleanOptionalAction,
                help="whether to enable or disable profiling",
                default=None)

    def handle(self,
               abort_scantag, abort_scannerjob, abort_scanstatus, log_level,
               profile, *args, **options):
        if abort_scannerjob:
            abort_scantag = messages.ScanTagFragment.from_json_object(
                    abort_scannerjob.statuses.last().scan_tag)
        elif abort_scanstatus:
            abort_scantag = messages.ScanTagFragment.from_json_object(
                    abort_scanstatus.scan_tag)

        msg = messages.CommandMessage(
                abort=abort_scantag,
                log_level=log_levels.get(log_level) if log_level else None,
                profiling=profile)
        logging.info(msg)

        with pika.PikaPipelineThread() as p:
            p.enqueue_message(
                    pika.ANON_QUEUE, msg.to_json_object(),
                    "broadcast", priority=10)
            p.enqueue_stop()
            p.run()
