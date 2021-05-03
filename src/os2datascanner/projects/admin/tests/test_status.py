import django
from datetime import datetime
from dateutil.tz import gettz
from django.utils.text import slugify

from os2datascanner.projects.admin.core.models.client import Client
from os2datascanner.projects.admin.organizations.models.organization import Organization
from os2datascanner.projects.admin.adminapp.models.scannerjobs.scanner_model import Scanner, ScanStatus


class StatusTest(django.test.TestCase):
    def setUp(self):
        client1 = Client.objects.create(name="client1")
        self.organization = Organization.objects.create(
            name="Magenta",
            uuid="b560361d-2b1f-4174-bb03-55e8b693ad0c",
            slug=slugify("Magenta"),
            client=client1,
        )
        self.scanner = Scanner(organization=self.organization)

    def test_estimates(self):
        ss = ScanStatus(
                scanner=self.scanner,
                scan_tag={"time": datetime.now(tz=gettz()).isoformat()})

        with self.subTest("empty"):
            self.assertEqual(
                    ss.fraction_explored,
                    None,
                    "exploration fraction should not have been defined yet")
            self.assertEqual(
                    ss.fraction_scanned,
                    None,
                    "scan fraction should not have been defined yet")
            self.assertFalse(
                    ss.finished,
                    "scan should not have finished yet")

        ss.total_sources = 2
        with self.subTest("start"):
            self.assertEqual(
                    ss.fraction_explored,
                    0.0,
                    "wrong exploration fraction")
            self.assertEqual(
                    ss.fraction_scanned,
                    None,
                    "scan fraction should not have been defined yet")
            self.assertFalse(
                    ss.finished,
                    "scan should not have finished yet")

        ss.explored_sources = 1
        ss.total_objects = 20
        with self.subTest("exploring"):
            self.assertEqual(
                    ss.fraction_explored,
                    0.5,
                    "wrong exploration fraction")
            self.assertEqual(
                    ss.fraction_scanned,
                    None,
                    "scan fraction should not have been defined yet")
            self.assertFalse(
                    ss.finished,
                    "scan should not have finished yet")

        ss.explored_sources = 2
        with self.subTest("scanning-1"):
            self.assertEqual(
                    ss.fraction_explored,
                    1.0,
                    "wrong exploration fraction")
            self.assertEqual(
                    ss.fraction_scanned,
                    0.0,
                    "wrong scan fraction")
            self.assertFalse(
                    ss.finished,
                    "scan should not have finished yet")

        ss.scanned_objects = 10
        with self.subTest("scanning-2"):
            self.assertEqual(
                    ss.fraction_scanned,
                    0.5,
                    "wrong scan fraction")
            self.assertFalse(
                    ss.finished,
                    "scan should not have finished yet")

        ss.scanned_objects = 20
        with self.subTest("scanned"):
            self.assertEqual(
                    ss.fraction_scanned,
                    1.0,
                    "wrong scan fraction")
            self.assertTrue(
                    ss.finished,
                    "scan should have finished")

    def test_broken(self):
        """Trying to derive properties for broken ScanStatus objects should
        fail cleanly."""
        ss = ScanStatus(
                scanner=self.scanner,
                scan_tag={"time": datetime.now(tz=gettz()).isoformat()},
                total_sources=5,
                explored_sources=5,
                total_objects=0)

        self.assertEqual(
                ss.fraction_scanned,
                None,
                "scan fraction should not have been defined")
