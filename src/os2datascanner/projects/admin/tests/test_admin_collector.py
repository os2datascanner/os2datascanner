from parameterized import parameterized
from django.db import transaction
from django.db.utils import DataError
from django.test import TestCase

from os2datascanner.utils.system_utilities import parse_isoformat_timestamp
from os2datascanner.engine2.model.file import (
        FilesystemHandle, FilesystemSource)
from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.rules.regex import RegexRule
from os2datascanner.engine2.rules.rule import Sensitivity

from ..adminapp.management.commands import pipeline_collector
from ..adminapp.management.commands.pipeline_collector import \
    status_message_received_raw, problem_message_recieved_raw
from ..adminapp.models.usererrorlog_model import UserErrorLog, translation_table
from ..adminapp.models.scannerjobs.scanner_model import ScheduledCheckup, ScanStatus, \
    Scanner

time0 = "2020-10-28T13:51:49+01:00"
time1 = "2020-10-28T14:21:27+01:00"
time2 = "2020-10-28T14:36:20+01:00"
scan_tag0 = messages.ScanTagFragment(
    scanner=messages.ScannerFragment(
            pk=22, name="Dummy test scanner"),
    time=parse_isoformat_timestamp(time0),
    user=None, organisation=None)
scan_tag1 = messages.ScanTagFragment(
    scanner=messages.ScannerFragment(
            pk=22, name="Dummy test scanner"),
    time=parse_isoformat_timestamp(time1),
    user=None, organisation=None)

common_rule = RegexRule("Vores hemmelige adgangskode er",
                        sensitivity=Sensitivity.WARNING)

common_handle = FilesystemHandle(
        FilesystemSource("/mnt/fs01.magenta.dk/brugere/af"),
        "OS2datascanner/Dokumenter/Verdensherredømme - plan.txt")

common_handle_corrupt = FilesystemHandle(
        FilesystemSource("/mnt/fs01.magenta.dk/brugere/af"),
        "/logo/Flag/Gr\udce6kenland.jpg")

common_scan_spec_corrupt = messages.ScanSpecMessage(
        scan_tag=scan_tag0,  # placeholder
        source=common_handle_corrupt.source,
        rule=common_rule,
        configuration={},
        filter_rule=None,
        progress=None)

common_scan_spec = messages.ScanSpecMessage(
        scan_tag=scan_tag1,  # placeholder
        source=common_handle.source,
        rule=common_rule,
        configuration={},
        filter_rule=None,
        progress=None)

# Positive MatchMessage objects.
positive_match_corrupt = messages.MatchesMessage(
        scan_spec=common_scan_spec_corrupt,
        handle=common_handle_corrupt,
        matched=True,
        matches=[
            messages.MatchFragment(
                rule=common_rule,
                matches=[{"dummy": "match object"}])
        ])

positive_match = messages.MatchesMessage(
        scan_spec=common_scan_spec,
        handle=common_handle,
        matched=True,
        matches=[
            messages.MatchFragment(
                rule=common_rule,
                matches=[{"dummy": "match object"}])
        ])

# ScanStatus message objects.
total_objects_scan_status = messages.StatusMessage(
    scan_tag=scan_tag0,
    message="dummy",
    total_objects=10,
    status_is_error=False)

message_scan_status = messages.StatusMessage(
    scan_tag=scan_tag0,
    message="dummy1",
    total_objects=0,
    status_is_error=True)

object_size_scan_status = messages.StatusMessage(
    scan_tag=scan_tag0,
    message="dummy2",
    status_is_error=False,
    object_type="some_type",
    object_size=100)


class PipelineCollectorTests(TestCase):

    @parameterized.expand([
        ("total objects update", total_objects_scan_status, 18020, "dummy",
         False, 0, 0),
        ("message update", message_scan_status, 0, "dummy1", True, 0, 0),
        ("object size update", object_size_scan_status, 0, "dummy2", False, 1, 100),
    ])
    def test_scan_status_update(self, _, scan_status_object, expected_total_objects,
                                expected_message, expected_is_error,
                                expected_scanned_objects, expected_scanned_size):
        scanner = Scanner.objects.create(name="dummy")
        scan_status_object = scan_status_object._deep_replace(
                scan_tag__scanner__pk=scanner.pk)
        ScanStatus.objects.create(
                scanner=scanner,
                scan_tag=scan_status_object.scan_tag.to_json_object(),
                total_sources=11,
                total_objects=expected_total_objects - 10
                if expected_total_objects > 0 else 0,
                scanned_objects=0,
                scanned_size=0)
        body = scan_status_object.to_json_object()
        [s for s in status_message_received_raw(body)]
        scan_status = ScanStatus.objects.get(scan_tag=body["scan_tag"])
        self.assertEqual(
            scan_status.total_objects, expected_total_objects,
            "total objects was not the expected.")
        self.assertEqual(
            scan_status.message, expected_message,
            "message was not the expected.")
        self.assertEqual(
            scan_status.status_is_error, expected_is_error,
            "status_is_error was not the expected.")
        self.assertEqual(
            scan_status.scanned_objects, expected_scanned_objects,
            "scanned_objects was not the expected.")
        self.assertEqual(
            scan_status.scanned_size, expected_scanned_size,
            "scanned_size was not the expected.")
        ScanStatus.objects.all().delete()
        Scanner.objects.all().delete()

    def test_surrogate_errors_are_caught(self):
        """How to test an exception is caught?
        We expect that no object is created if a DataError occurs. Reason being
        if it is the file path (as in this case) that is corrupt we cannot visit
        the file again, and then there is no reason to store the data.
        We could consider checking the file path. For now, we log the dataerror.
        """
        try:
            with transaction.atomic():
                pipeline_collector.update_scheduled_checkup(
                        handle=positive_match_corrupt.handle,
                        matches=positive_match_corrupt,
                        problem=None,
                        scan_time=positive_match_corrupt.scan_spec.scan_tag.time,
                        scanner=None)
        except DataError:
            # Expected behaviour
            pass

        with self.assertRaises(DataError):
            ScheduledCheckup.objects.select_for_update().get(
                handle_representation=positive_match_corrupt.handle.to_json_object())

    def test_problem_message_is_logged(self):
        """Test that a UserErrorLog object is successfully created when the pipeline_collector
        recieves a problem message."""
        scan_spec = common_scan_spec
        scan_tag = scan_spec.scan_tag
        handle = common_handle
        error_message = "Exploration error. MemoryError: 12, Cannot allocate memory"

        problem_message = messages.ProblemMessage(
            scan_tag=scan_tag, source=scan_spec.source, handle=handle,
            message=error_message)
        body = problem_message.to_json_object()
        yield from problem_message_recieved_raw(body)

        self.assertTrue(UserErrorLog.objects.all().exists())
        self.assertEqual(
            UserErrorLog.objects.first().user_friendly_error_message,
            translation_table[error_message]
        )
