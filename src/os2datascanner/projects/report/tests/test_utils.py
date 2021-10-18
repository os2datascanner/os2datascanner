from django.test import TestCase

from ..reportapp.management.commands import pipeline_collector
from ..reportapp.utils import get_max_sens_prop_value
from ..reportapp.models.documentreport_model import DocumentReport

from .generate_test_data import \
    get_positive_match_with_probability_and_sensitivity


class UtilsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.generate_match(
            get_positive_match_with_probability_and_sensitivity())

    @classmethod
    def generate_match(cls, match):
        prev, new = pipeline_collector.get_reports_for(
            match.handle.to_json_object(),
            match.scan_spec.scan_tag)
        pipeline_collector.handle_match_message(
            prev, new, match.to_json_object())

    def test_get_max_sens_prop_value(self):
        self.assertEqual(1.0,
                         get_max_sens_prop_value(
                             DocumentReport.objects.first(),
                             'probability')
                         )
        self.assertEqual(1000,
                         get_max_sens_prop_value(
                             DocumentReport.objects.first(),
                             'sensitivity').value
                         )
