from os import getenv
import sys
from json import dumps, loads
import unittest
import subprocess


from os2datascanner.engine2.model.core import Source
from os2datascanner.engine2.pipeline.utilities import PikaPipelineRunner


from .test_engine2_pipeline import (
        handle_message, data_url, rule, expected_matches)


def python(*args):
    """Starts a new instance of this Python interpreter with the specified
    arguments. Standard output and standard error will be passed through."""
    return subprocess.Popen([sys.executable, *args])


class StopHandling(Exception):
    pass


class SubprocessPipelineTestRunner(PikaPipelineRunner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages = {}

    def handle_message(self, message_body, *, channel=None):
        self.messages[message_body["origin"]] = message_body
        if len(self.messages) == 2:
            raise StopHandling()
        yield from []


class Engine2SubprocessPipelineTests(unittest.TestCase):
    def setUp(self):

        self.runner = SubprocessPipelineTestRunner(
                read=["os2ds_results"],
                write=["os2ds_scan_specs"],
                heartbeat=6000)

        python("-m", "os2datascanner.engine2.pipeline._consume_queue",
                "os2ds_scan_specs", "os2ds_conversions",
                "os2ds_representations", "os2ds_matches", "os2ds_handles",
                "os2ds_metadata", "os2ds_problems", "os2ds_results").wait()
        self.explorer = python(
                "-m", "os2datascanner.engine2.pipeline.explorer")
        self.processor = python(
                "-m", "os2datascanner.engine2.pipeline.processor")
        self.matcher = python(
                "-m", "os2datascanner.engine2.pipeline.matcher")
        self.tagger = python(
                "-m", "os2datascanner.engine2.pipeline.tagger")
        self.exporter = python(
                "-m", "os2datascanner.engine2.pipeline.exporter")

    def tearDown(self):
        self.runner.clear()
        for p in (self.explorer, self.processor, self.matcher, self.tagger,
                self.exporter):
            p.kill()
            p.wait()

    def test_simple_regex_match(self):
        print(Source.from_url(data_url).to_json_object())
        obj = {
            "scan_tag": "integration_test",
            "source": Source.from_url(data_url).to_json_object(),
            "rule": rule.to_json_object()
        }

        self.runner.channel.basic_publish(exchange='',
                routing_key="os2ds_scan_specs",
                body=dumps(obj).encode())

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
