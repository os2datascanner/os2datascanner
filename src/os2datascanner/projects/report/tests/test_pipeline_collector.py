from django.test import TestCase
import unittest

from os2datascanner.utils.system_utilities import parse_isoformat_timestamp
from os2datascanner.engine2.model.file import (
        FilesystemHandle, FilesystemSource)
from os2datascanner.engine2.rules.regex import RegexRule
from os2datascanner.engine2.rules.logical import AndRule
from os2datascanner.engine2.rules.last_modified import LastModifiedRule
from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.conversions.types import OutputType
from ..reportapp.models.documentreport_model import DocumentReport
from ..reportapp.management.commands import pipeline_collector


time0 = "2020-10-28T13:51:49+01:00"
time1 = "2020-10-28T14:21:27+01:00"
time2 = "2020-10-28T14:36:20+01:00"
scan_tag0 = {
    "scanner": "Dummy test scanner",
    "time": time0
}
scan_tag1 = {
    "scanner": "Dummy test scanner",
    "time": time1
}
scan_tag2 = {
    "scanner": "Dummy test scanner",
    "time": time2
}


common_handle = FilesystemHandle(
        FilesystemSource("/mnt/fs01.magenta.dk/brugere/af"),
        "OS2datascanner/Dokumenter/Verdensherredømme - plan.txt")
common_rule = RegexRule("Vores hemmelige adgangskode er")
common_scan_spec = messages.ScanSpecMessage(
        scan_tag=None, # placeholder
        source=common_handle.source,
        rule=common_rule,
        configuration={},
        progress=None)

positive_match = messages.MatchesMessage(
        scan_spec=common_scan_spec._replace(scan_tag=scan_tag0),
        handle=common_handle,
        matched=True,
        matches=[messages.MatchFragment(
                rule=common_rule,
                matches={"dummy": "match object"})])
negative_match = messages.MatchesMessage(
        scan_spec=common_scan_spec._replace(scan_tag=scan_tag1),
        handle=common_handle,
        matched=False,
        matches=[messages.MatchFragment(
                rule=common_rule,
                matches=[])])
deletion = messages.ProblemMessage(
        scan_tag=scan_tag1,
        source=None,
        handle=common_handle,
        message="There was a file here. It's gone now.",
        missing=True)

late_rule = LastModifiedRule(parse_isoformat_timestamp(time2))
late_negative_match = messages.MatchesMessage(
        scan_spec=common_scan_spec._replace(
                scan_tag=scan_tag2,
                rule=AndRule(
                        late_rule,
                        common_rule)),
        handle=common_handle,
        matched=False,
        matches=[messages.MatchFragment(
                rule=late_rule,
                matches=[])])


class PipelineCollectorTests(TestCase):
    def test_rejection(self):
        """Failed match messages shouldn't be stored in the database."""
        prev, new = pipeline_collector.get_reports_for(
                negative_match.handle.to_json_object(),
                negative_match.scan_spec.scan_tag)
        pipeline_collector.handle_match_message(
                prev, new, negative_match.to_json_object())
        self.assertEqual(
                new.pk,
                None,
                "negative match was saved anyway")

    def test_acceptance(self):
        """Successful match messages should be stored in the database."""
        prev, new = pipeline_collector.get_reports_for(
                positive_match.handle.to_json_object(),
                positive_match.scan_spec.scan_tag)
        pipeline_collector.handle_match_message(
                prev, new, positive_match.to_json_object())
        self.assertNotEqual(
                new.pk,
                None,
                "positive match was not saved")
        self.assertEqual(
                new.resolution_status,
                None,
                "fresh match was already resolved")
        self.assertEqual(
                new.scan_time.isoformat(),
                positive_match.scan_spec.scan_tag["time"],
                "match time was not taken from scan specification")
        return new

    def test_edit(self):
        """Removing matches from a file should update the status of the
        previous match message."""
        saved_match = self.test_acceptance()
        self.test_rejection()
        saved_match.refresh_from_db()
        self.assertEqual(
                saved_match.resolution_status,
                DocumentReport.ResolutionChoices.EDITED.value,
                "resolution status not correctly updated")

    def test_removal(self):
        """Deleting a file should update the status of the previous match
        message."""
        saved_match = self.test_acceptance()

        prev, new = pipeline_collector.get_reports_for(
                deletion.handle.to_json_object(),
                deletion.scan_tag)
        pipeline_collector.handle_problem_message(
                prev, new, deletion.to_json_object())

        saved_match.refresh_from_db()
        self.assertEqual(
                saved_match.resolution_status,
                DocumentReport.ResolutionChoices.REMOVED.value,
                "resolution status not correctly updated")

    def test_recycler(self):
        """Receiving a failed match message which failed because of the
        Last-Modified check should update the timestamp of the previous match
        message, but should not create a new database object."""
        saved_match = self.test_acceptance()

        prev, new = pipeline_collector.get_reports_for(
                late_negative_match.handle.to_json_object(),
                late_negative_match.scan_spec.scan_tag)
        pipeline_collector.handle_match_message(
                prev, new, late_negative_match.to_json_object())

        self.assertEqual(
                new.pk,
                None,
                "negative match was saved anyway")
        saved_match.refresh_from_db()
        self.assertEqual(
                saved_match.scan_time,
                parse_isoformat_timestamp(time2),
                "match timestamp not correctly updated")
