import random
from recurrence.base import Recurrence
from os2datascanner.projects.admin.adminapp.models.rules.cprrule_model import CPRRule
from os2datascanner.projects.admin.adminapp.models.scannerjobs.webscanner_model import WebScanner

from os2datascanner.projects.admin.organizations.models.organization import Organization
from os2datascanner.projects.admin.adminapp.models.scannerjobs.scanner_model import ScanStatus
from os2datascanner.projects.admin.adminapp.management.commands.list_scannerjobs import \
        Command as list_scannerjobs
import requests
import uuid
import unittest


class WebScanIntegrationTest(unittest.TestCase):

    def tearDown(self) -> None:
        for scanner_object in self.scanner_objects:
            scan_model = self.scanner_objects[scanner_object]["webscan"]
            scan_model.delete()

    def test_scan_finds_all_sources(self):
        """Tests whether a scan finds all files in a websource."""
        amount_of_scans = 2
        self.scanner_objects = {}

        for _ in range(amount_of_scans):
            matches = random.randrange(1, 100)
            sub_files = random.randrange(1, 50)
            seed, scan = self.create_scan(matches, sub_files)
            self.scanner_objects[seed] = scan

        for scan_uuid in self.scanner_objects:
            scan = self.scanner_objects[scan_uuid]["webscan"]
            scan_status = scan.run()
            self.scanner_objects[scan_uuid]["scan_status"] = scan_status

        self.await_scans(self.scanner_objects)
        completed_scans = list_scannerjobs().list_scannerjobs()

        self.assert_amount_of_sources_per_scan(completed_scans, self.scanner_objects)

    def assert_amount_of_sources_per_scan(self, completed_scans, scanner_objects):
        """ Goes through each scan and asserts that the scan has the
            correct amount of sources found"""
        for scan_name in completed_scans:
            if scan_name in scanner_objects:
                actual_scan = completed_scans[scan_name]
                _, seed, _, scanned_objects = list(actual_scan.values())
                _, _, sub_files, scan_url, _ = list(scanner_objects[seed].values())

                # Add one as sub_files does not include the index/landing page
                expected_scanned_objects = int(sub_files) + 1
                self.assertEquals(
                    expected_scanned_objects, scanned_objects,
                    f"Expected {expected_scanned_objects} sources, found {scanned_objects}\n"
                    + f"link: {scan_url}")

    def await_scans(self, scanner_objects):
        """ Looks for the scans created by the test
        and return when they have the status finished """
        scans_running = True
        while scans_running:
            running_scans = []
            for scan_uuid in scanner_objects:
                scan_status = ScanStatus.objects.filter(
                        scan_tag=scanner_objects[scan_uuid]["scan_status"]).first()
                if not scan_status.finished:
                    running_scans.append(scan_status)
            if len(running_scans) < 1:
                scans_running = False

    def create_scan(self, matches, sub_files):
        """Creates a webscan and returns the relevant specs"""
        seed = str(uuid.uuid1())
        # should mirror the settings of the engine for http_ttl
        max_depth = 25
        response = requests.get(
                "http://datasynth:5010/websource"
                + f"?seed={seed}&sub_files={sub_files}&depth={max_depth}"
                + '&matches={"010180-0008":' + str(matches) + '}'
                ).json()
        scan_url = response["reference"]
        org = Organization.objects.first()
        recurrence = Recurrence()
        webscanner, created = WebScanner.objects.get_or_create(
            name=seed,
            url=scan_url,
            validation_status=True,
            do_last_modified_check=False,
            organization=org,
            schedule=recurrence,
            download_sitemap=False,
        )
        print("scan url is : ", scan_url)
        if created:
            cpr = CPRRule.objects.first()
            webscanner.rules.set([cpr])
        return seed, {
            "webscan": webscanner,
            "matches": matches,
            "sub_files": sub_files,
            "scan_url": scan_url}
