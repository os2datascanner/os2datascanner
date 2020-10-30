#!/usr/bin/env python
# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2datascanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (https://os2.eu/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( https://os2.eu/ )

from django.core.management.base import BaseCommand

from os2datascanner.utils.system_utilities import parse_isoformat_timestamp
from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.pipeline.utilities.pika import PikaPipelineRunner
from ...models.scannerjobs.scanner_model import Scanner, ScheduledCheckup


def message_received_raw(body):
    handle = None
    scan_tag = None
    if "problem" in body:
        problem = messages.ProblemMessage.from_json_object(body)
        handle = problem.handle
        scan_tag = problem.scan_tag
        # XXX: ideally we'd detect if a LastModifiedRule fails so that we can
        # preserve the date to scan the file properly next time, but we don't
        # (yet) get enough information out of the pipeline for that
    elif "matches" in body:
        matches = messages.MatchesMessage.from_json_object(body)
        # We're only interested in messages that reflect a match
        if matches.matched:
            handle = matches.handle
            scan_tag = matches.scan_spec.scan_tag

    if not scan_tag or not handle:
        return

    ScheduledCheckup.objects.create(
            handle_representation=handle.to_json_object(),
            scanner=Scanner.objects.get(pk=scan_tag["scanner"]["pk"]),
            interested_before=parse_isoformat_timestamp(scan_tag["time"]))

    yield from []


class AdminCollector(PikaPipelineRunner):
    def handle_message(self, message_body, *, channel=None):
        return message_received_raw(message_body)


class Command(BaseCommand):
    """Command for starting a pipeline collector process."""
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "--checkups",
            type=str,
            help="the name of the AMQP queue from which checkup requests"
                 + " should be read",
            default="os2ds_checkups")

    def handle(self, checkups, *args, **options):
        with AdminCollector(read=[checkups], heartbeat=6000) as runner:
            try:
                print("Start")
                runner.run_consumer()
            finally:
                print("Stop")
