import os.path
from copy import deepcopy
import base64
import unittest

from os2datascanner.engine2.model.core import Source, SourceManager
from os2datascanner.engine2.model.file import FilesystemSource
from os2datascanner.engine2.rules.rule import Sensitivity
from os2datascanner.engine2.rules.cpr import CPRRule
from os2datascanner.engine2.rules.regex import RegexRule
from os2datascanner.engine2.rules.logical import OrRule
from os2datascanner.engine2.pipeline import (
        explorer, processor, matcher, tagger, exporter)


here_path = os.path.dirname(__file__)
test_data_path = os.path.join(here_path, "..", "data")


data = """Hwæt! wē Gār-Dena in gēar-dagum
þēod-cyninga þrym gefrūnon,
hū ðā æþeling as ell en fremedon.
Oft Scyld Scēfing sceaþena þrēatum,
monegum mǣgþum meodo-setla oftēah."""
data_url = "data:text/plain;base64,{0}".format(
       base64.encodebytes(data.encode("utf-8")).decode("ascii"))

rule = OrRule(
        RegexRule("Æthelred the Unready", name="Check for ill-advised kings"),
        RegexRule("Scyld S(.*)g", sensitivity=Sensitivity.CRITICAL),
        RegexRule("Professor James Moriarty"))

expected_matches = [
    {
        "rule": {
            "type": "regex",
            "name": "Check for ill-advised kings",
            "sensitivity": None,
            "expression": "Æthelred the Unready"
        },
        "matches": None
    },
    {
        "rule": {
            "type": "regex",
            "name": None,
            "sensitivity": Sensitivity.CRITICAL.value,
            "expression": "Scyld S(.*)g"
        },
        "matches": [
            {
                "offset": 98,
                "match": "Scyld Scēfing",
                # context is 50 char before and after the match(13 char)
                "context": data[98-50:98+13+50],
                "context_offset": 98-50,
            }
        ]
    }
]


raw_scan_spec = {
    "scan_tag": {
        "scanner": {
            "name": "integration_test",
            "pk": 0
        },
        "user": None,
        "organisation": "Vejstrand Kommune",
        "time": "2020-01-01T00:00:00+00:00"
    },
    "source": Source.from_url(data_url).to_json_object(),
    "rule": rule.to_json_object()
}


class StopHandling(Exception):
    pass


def handle_message(body, channel):
    with SourceManager() as sm:
        if channel == "os2ds_scan_specs":
            yield from explorer.message_received_raw(body, channel, sm)
        elif channel == "os2ds_conversions":
            yield from processor.message_received_raw(body, channel, sm)
        elif channel == "os2ds_representations":
            yield from matcher.message_received_raw(body, channel, sm)
        elif channel == "os2ds_handles":
            yield from tagger.message_received_raw(body, channel, sm)
        elif channel in ("os2ds_matches", "os2ds_metadata", "os2ds_problems"):
            yield from exporter.message_received_raw(body, channel, sm)
        # "os2ds_status" messages get dropped on the floor


class Engine2PipelineTests(unittest.TestCase):
    def setUp(self):
        self.messages = []
        self.unhandled = []

    def run_pipeline(self, runner=handle_message, **runner_kwargs):
        while self.messages:
            (body, channel), self.messages = self.messages[0], self.messages[1:]
            if channel != "os2ds_results":
                for channel, body in runner(body, channel, **runner_kwargs):
                    self.messages.append((body, channel,))
            else:
                self.unhandled.append((body, channel,))

    def test_simple_regex_match(self):
        self.messages.append((raw_scan_spec, "os2ds_scan_specs",))
        self.run_pipeline()

        self.assertEqual(
                len(self.unhandled),
                2)
        results = {body["origin"]: body for body, _ in self.unhandled}

        self.assertTrue(
                results["os2ds_matches"]["matched"],
                "RegexRule match failed")
        self.assertEqual(
                results["os2ds_matches"]["matches"],
                expected_matches,
                "RegexRule match did not produce expected result")

    def test_unsupported_sources(self):
        obj = deepcopy(raw_scan_spec)
        obj["source"] = {
            "type": "forbidden-knowledge",
            "of": ["good", "evil"]
        }

        self.messages.append((obj, "os2ds_scan_specs",))
        self.run_pipeline()

        self.assertEqual(
                len(self.unhandled),
                1)
        self.assertEqual(
                self.unhandled[0][0]["origin"],
                "os2ds_problems")

    def test_ocr_skip(self):
        obj = deepcopy(raw_scan_spec)
        obj["source"] = (
                FilesystemSource(os.path.join(
                        test_data_path, "ocr", "good")
                ).to_json_object())
        obj["rule"] = (
                CPRRule(
                        modulus_11=False, ignore_irrelevant=False
                ).to_json_object())
        obj["configuration"] = {
            "skip_mime_types": ["image/*"]
        }

        self.messages.append((obj, "os2ds_scan_specs",))
        self.run_pipeline()

        for message, queue in self.unhandled:
            if queue == "os2ds_results":
                self.assertFalse(
                    message["matched"],
                    "OCR match found with OCR disabled")
            else:
                self.fail("unexpected message in queue {0}".format(queue))

    def test_corrupted_container(self):
        obj = deepcopy(raw_scan_spec)
        obj["source"] = (
                FilesystemSource(
                        os.path.join(test_data_path, "pdf", "corrupted")
                ).to_json_object())
        obj["rule"] = (
                CPRRule(
                        modulus_11=False, ignore_irrelevant=False
                ).to_json_object())

        self.messages.append((obj, "os2ds_scan_specs",))
        self.run_pipeline()

        self.assertEqual(
                len(self.unhandled),
                1)
        self.assertEqual(
                self.unhandled[0][0]["origin"],
                "os2ds_problems")

    def test_rule_crash(self):
        obj = deepcopy(raw_scan_spec)
        obj["rule"] = {
            "type": "buggy"
        }

        self.messages.append((obj, "os2ds_scan_specs",))
        self.run_pipeline()

        self.assertEqual(
                len(self.unhandled),
                1)
        self.assertEqual(
                self.unhandled[0][0]["origin"],
                "os2ds_problems")
