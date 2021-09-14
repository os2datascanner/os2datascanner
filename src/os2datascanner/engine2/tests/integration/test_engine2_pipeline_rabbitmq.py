from json import dumps, loads
import unittest


from os2datascanner.engine2.model.core import Source
from os2datascanner.engine2.pipeline.utilities.pika import PikaPipelineThread


from .test_engine2_pipeline import (
        handle_message, data_url, rule, expected_matches)


class PipelineTestRunner(PikaPipelineThread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.messages = {}

    def handle_message(self, routing_key, body):
        if routing_key != "os2ds_results":
            yield from handle_message(body, routing_key)
        else:
            self.messages[body["origin"]] = body
            if len(self.messages) == 2:
                raise StopHandling()


class StopHandling(Exception):
    pass


class Engine2PipelineTests(unittest.TestCase):
    def setUp(self):
        self.runner = PipelineTestRunner(
                read=["os2ds_scan_specs", "os2ds_conversions",
                        "os2ds_representations", "os2ds_matches",
                        "os2ds_handles", "os2ds_metadata",
                        "os2ds_problems", "os2ds_results"],
                write=["os2ds_scan_specs"],
                heartbeat=6000)

    def tearDown(self):
        self.runner.clear()

    def test_simple_regex_match(self):
        print(Source.from_url(data_url).to_json_object())
        obj = {
            "scan_tag": {
                "scanner": {
                    "name": "integration_test",
                    "pk": 0
                },
                "time": "2020-01-01T00:00:00+00:00",
                "user": None,
                "organisation": "Vejstrand Kommune"
            },
            "source": Source.from_url(data_url).to_json_object(),
            "rule": rule.to_json_object()
        }

        self.runner.enqueue_message("os2ds_scan_specs", obj)

        try:
            self.runner.run_consumer()
        except StopHandling as e:
            self.assertTrue(
                    self.runner.messages["os2ds_matches"]["matched"],
                    "RegexRule match failed")
            self.assertEqual(
                    self.runner.messages["os2ds_matches"]["matches"],
                    expected_matches,
                    "RegexRule match did not produce expected result")
