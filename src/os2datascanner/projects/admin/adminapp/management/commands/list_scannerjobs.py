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

from django.core.management import BaseCommand

from os2datascanner.projects.admin.adminapp.models.scannerjobs.scanner_model import (
    Scanner, ScanStatus, ScheduledCheckup, )


class Command(BaseCommand):
    """
        This command lists all scanner jobs and the following attributes:
        PK
        Name
        Start time
        Number of objects scanned
        Scan status as bool
        Checkup messages as count()
    """

    help = "List all scannerjobs and some of their attributes."

    def handle(self, *args, **options):

        for scannerjob in Scanner.objects.all():
            pk = scannerjob.pk
            name = scannerjob.name
            start_time = None
            scanned_objects = None
            scan_status = None
            check_up_msgs = ScheduledCheckup.objects.filter(scanner=scannerjob.pk).count()

            if ScanStatus.objects.filter(scanner=scannerjob.pk).exists():
                # We are only interested in the most recent ScanStatus object,
                # but there's likely more than one, hence we filter .last()
                scan_status_obj = ScanStatus.objects.filter(scanner=scannerjob.pk).last()

                start_time = scan_status_obj.start_time
                scanned_objects = scan_status_obj.scanned_objects
                scan_status = scan_status_obj.finished

            self.stdout.write(self.style.SUCCESS(
                f'\nScanner PK: {pk} \nScanner Name: {name} \n'
                f'Start Time: {start_time} \nScanned Objects: {scanned_objects} \n'
                f'Scan Status Finished(T/F): {scan_status} \n'
                f'Check-up Msg Obj Count: {check_up_msgs}\n'))
