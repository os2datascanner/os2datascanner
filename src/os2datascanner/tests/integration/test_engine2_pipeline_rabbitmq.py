from os import getenv
from json import dumps, loads
import pika
import unittest


from os2datascanner.engine2.pipeline.utilities import PikaPipelineRunner
from os2datascanner.engine2.model.core import Source


from .test_engine2_pipeline import (
        handle_message, data_url, rule, expected_matches)


class PipelineTestRunner(PikaPipelineRunner):
    def handle_message(self, message_body, *, channel=None):
        yield from handle_message(message_body, channel)


class StopHandling(Exception):
    pass


class Engine2PipelineTests(unittest.TestCase):
    def setUp(self):
        self.runner = PipelineTestRunner(
                read=["os2ds_scan_specs", "os2ds_conversions",
                        "os2ds_representations", "os2ds_matches",
                        "os2ds_handles", "os2ds_metadata",
                        "os2ds_problems"],
                write=["os2ds_results"],
                host=getenv("AMQP_HOST", "localhost"),
                heartbeat=6000)

    def tearDown(self):
        self.runner.clear()

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

        messages = {}

        def result_received(channel, method, properties, body):
            channel.basic_ack(method.delivery_tag)
            body = loads(body.decode("utf-8"))
            messages[body["origin"]] = body
            if len(messages) == 2:
                raise StopHandling()

        self.runner.channel.basic_consume("os2ds_results", result_received)

        try:
            self.runner.run_consumer()
        except StopHandling as e:
            self.assertTrue(
                    messages["os2ds_matches"]["matched"],
                    "RegexRule match failed")
            self.assertEqual(
                    messages["os2ds_matches"]["matches"],
                    expected_matches,
                    "RegexRule match did not produce expected result")
