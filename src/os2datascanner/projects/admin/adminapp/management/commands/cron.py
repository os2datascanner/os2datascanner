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

"""Program meant to be run once a minute by cron.

Starts spiders scheduled to run during the current minute.
"""

import datetime
from dateutil import tz

from django.core.management.base import BaseCommand

from os2datascanner.utils.system_utilities import time_now
from ...models.scannerjobs.scanner import Scanner


current_qhr = time_now().replace(second=0)
current_qhr = current_qhr.replace(
    minute=current_qhr.minute - current_qhr.minute % 15
)

next_qhr = current_qhr + datetime.timedelta(
    minutes=15, microseconds=-1
)


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "--now",
            metavar="now",
            type=bool,
            default=False,
            help="Run the scanner now if scheduled for today")

    def handle(self, *args, now=False, **kwargs):
        # Loop through all scanners
        for scanner in Scanner.objects.exclude(schedule="").select_subclasses():
            # Skip scanners that should not start now
            start_time = scanner.get_start_time()
            if ((start_time < current_qhr.time() or start_time > next_qhr.time())
                    and not now):
                continue

            try:
                # Parse the recurrence rule expression
                schedule = scanner.schedule
            except ValueError as e:
                # This shouldn't happen because we should validate in the UI
                reason = "Invalid schedule expression: %s" % e
                print(reason)
                continue

            # We have to set the times of the specific dates to the start time in
            # order for the recurrence rule check to work
            for i in range(len(schedule.rdates)):
                rdate = schedule.rdates[i]
                schedule.rdates[i] = rdate.replace(hour=start_time.hour,
                                                   minute=start_time.minute)

            # Check if it's time to run the scanner
            if not schedule.between(
                current_qhr, next_qhr,
                # Generate recurrences starting from current quarter 2014/01/01
                dtstart=datetime.datetime(
                    2014, 1, 1, current_qhr.hour, current_qhr.minute,
                    tzinfo=tz.gettz()),
                inc=True
            ):
                continue

            print("Running scanner %s" % scanner)
            scanner.run()
