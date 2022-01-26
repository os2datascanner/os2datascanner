from django.test import TestCase

from os2datascanner.utils.system_utilities import parse_isoformat_timestamp
from os2datascanner.engine2.model.file import (
        FilesystemHandle, FilesystemSource)
from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.rules.regex import RegexRule
from os2datascanner.engine2.rules.rule import Sensitivity

from ..adminapp.management.commands import pipeline_collector
from ..adminapp.models.scannerjobs.scanner_model import ScheduledCheckup

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
        progress=None)

common_scan_spec = messages.ScanSpecMessage(
        scan_tag=scan_tag1,  # placeholder
        source=common_handle.source,
        rule=common_rule,
        configuration={},
        progress=None)

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


class PipelineCollectorTests(TestCase):

    def test_surrogate_errors_are_caught(self):
        """How to test an exception is caught?
        We expect that no object is created if a DataError occurs. Reason being
        if it is the file path (as in this case) that is corrupt we cannot visit
        the file again, and then there is no reason to store the data.
        We could consider checking the file path. For now, we log the dataerror.
        """
        pipeline_collector.update_scheduled_checkup(
                handle=positive_match_corrupt.handle,
                matches=positive_match_corrupt,
                problem=None,
                scan_time=positive_match_corrupt.scan_spec.scan_tag.time,
                scanner=None)

        from django.db.utils import DataError
        with self.assertRaises(DataError):
            ScheduledCheckup.objects.select_for_update().get(
                handle_representation=positive_match_corrupt.handle.to_json_object())
