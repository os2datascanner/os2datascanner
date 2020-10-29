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

from os2datascanner.engine2.pipeline.utilities.pika import PikaPipelineRunner
from ...models.scannerjobs.scanner_model import ScheduledCheckup


class AdminCollector(PikaPipelineRunner):
    def handle_message(self, message_body, *, channel=None):
        pass


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
