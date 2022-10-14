from django.test import TestCase
from datetime import datetime
from dateutil.tz import gettz
from django.utils.text import slugify

from os2datascanner.utils.system_utilities import time_now
from os2datascanner.engine2.pipeline import messages
from os2datascanner.projects.admin.core.models.client import Client
from os2datascanner.projects.admin.organizations.models.organization import Organization
from os2datascanner.projects.admin.adminapp.models.scannerjobs.scanner import (
        Scanner, ScanStatus)

from os2datascanner.projects.admin.adminapp.management.commands import status_collector


def record_status(status):
    """Records a status message to the database as though it were received by
    the administration system's pipeline collector."""
    return list(status_collector.status_message_received_raw(
            status.to_json_object()))


class StatusTest(TestCase):
    def setUp(self):
        client1 = Client.objects.create(name="client1")
        self.organization = Organization.objects.create(
            name="Magenta",
            uuid="b560361d-2b1f-4174-bb03-55e8b693ad0c",
            slug=slugify("Magenta"),
            client=client1,
        )
        self.scanner = Scanner.objects.create(
                name="Do unspecified action(s)(?)",
                organization=self.organization)

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
                scan_tag={"time": time_now().isoformat()},
                total_sources=5,
                explored_sources=5,
                total_objects=0)

        self.assertEqual(
                ss.fraction_scanned,
                None,
                "scan fraction should not have been defined")

    def test_no_updates_on_save(self):
        ss = ScanStatus(
            scanner=self.scanner,
            scan_tag={"time": time_now().isoformat()},
            total_sources=5,
            explored_sources=5,
            total_objects=0,
        )
        self.scanner.save()
        ss.save()
        last_modified = ss.last_modified
        # save should not update last_modified field on scannerStatus
        ss.save()

        self.assertEqual(
            last_modified,
            ss.last_modified,
            "scanStatus does update last modifed on save",
        )

        ss.delete()
        self.scanner.delete()

    def test_counting_broken_sources(self):
        dummy_scan_tag = messages.ScanTagFragment(
                time=time_now(),
                user=None,
                scanner=messages.ScannerFragment(
                        pk=self.scanner.pk,
                        name=self.scanner.name),
                organisation=None)

        ss = ScanStatus.objects.create(
                scanner=self.scanner,
                scan_tag=dummy_scan_tag.to_json_object(),
                total_sources=5,
                explored_sources=0,
                total_objects=0)

        error = "Exploration error. None: a, b, c, d, e"

        record_status(messages.StatusMessage(
                scan_tag=dummy_scan_tag,
                total_objects=20,
                message="", status_is_error=False))

        for _ in range(0, 4):
            record_status(messages.StatusMessage(
                    scan_tag=dummy_scan_tag,
                    total_objects=0,
                    message=error,
                    status_is_error=True))

        ss.refresh_from_db()
        self.assertEqual(
                ss.explored_sources,
                5,
                "failing Sources were not counted")
