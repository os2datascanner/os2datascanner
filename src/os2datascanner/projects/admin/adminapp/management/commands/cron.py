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
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )

from os import getenv
import logging
import datetime

from django.core.management.base import BaseCommand

from os2datascanner.utils.log_levels import log_levels
from os2datascanner.utils.system_utilities import time_now
from ...models.scannerjobs.scanner import Scanner, ScanStatus


logger = logging.getLogger(__name__)

current_qhr = time_now().replace(second=0)
current_qhr = current_qhr.replace(
    minute=current_qhr.minute - current_qhr.minute % 15
)

next_qhr = current_qhr + datetime.timedelta(minutes=15)


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
                "--now",
                action="store_true",
                help="run the scanner now if scheduled for today")
        parser.add_argument(
                "--log",
                default=None,
                help="change the level at which log messages will be printed",
                choices=log_levels.keys())

    def handle(self, *args, now, log, **options):
        if log is None:
            log = getenv("LOG_LEVEL", "info")

        # Change formatting to include datestamp
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(format=fmt, datefmt='%Y-%m-%d %H:%M:%S')
        # Set level for root logger
        logging.getLogger("os2datascanner").setLevel(log_levels[log])

        # Loop through all scanners
        for scanner in Scanner.objects.exclude(schedule="").select_subclasses():
            qs, qe = (current_qhr.time(), next_qhr.time())
            start = False
            match (scanner.schedule_date, scanner.schedule_time):
                case (datetime.date() as d, datetime.time() as t) \
                        if d == current_qhr.date() and t >= qs and t < qe:
                    logger.info(
                            f"{scanner!r} is scheduled to run now, starting"
                            " it")
                    start = True
                case (datetime.date() as d, datetime.time() as t) \
                        if d == current_qhr.date() and now:
                    logger.info(
                            f"{scanner!r} is scheduled to run today and"
                            " --now is set, starting it")
                    start = True
                case (datetime.date() as d, datetime.time() as t) \
                        if d == current_qhr.date():
                    logger.debug(
                            f"{scanner!r} is scheduled to run today, but scan"
                            f" time {t} does not fall within [{qs}, {qe})")
                case (datetime.date() as d, _):
                    logger.debug(
                            f"{scanner!r} is not scheduled to run today. Next"
                            f" scan date is {d}")
                case (a, b):
                    logger.debug(
                            f"Not running {scanner!r} for some reason"
                            f" (a={a}, b={b})")

            if start:
                # In principle we should start this scanner now. Check that
                # it's not already running, though
                ScanStatus.clean_defunct()

                last_status = scanner.statuses.last()
                if last_status is None or last_status.finished:
                    scanner.run()
                else:
                    logger.warning(
                            f"{scanner!r} is already running, not starting it"
                            " again")
