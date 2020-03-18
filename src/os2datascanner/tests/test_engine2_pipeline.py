import unittest

from os2datascanner.engine2.rules.rule import Sensitivity
from os2datascanner.engine2.pipeline.messages import MatchesMessage


class Engine2PipelineTests(unittest.TestCase):
    def test_rule_sensitivity(self):
        message = MatchesMessage(
            scan_spec={}, # unused (at present)
            handle=None, # unused (at present)
            matched=True,
            matches=[
                {
                    "rule": {
                        "type": "fictional",
                        "sensitivity": 1000
                    },
                    "matches": [
                        {
                            "match": True
                        },
                        {
                            "match": True
                        },
                        {
                            "match": True,
                            "sensitivity": None
                        }
                    ]
                }
            ]
        )

        self.assertEqual(
                message.sensitivity,
                Sensitivity.CRITICAL,
                "rule sensitivity failed")

    def test_match_sensitivity(self):
        message = MatchesMessage(
            scan_spec={}, # unused (at present)
            handle=None, # unused (at present)
            matched=True,
            matches=[
                {
                    "rule": {
                        "type": "fictional",
                        "sensitivity": 1000
                    },
                    "matches": [
                        {
                            "match": True,
                            "sensitivity": 250
                        },
                        {
                            "match": True,
                            "sensitivity": 750
                        },
                        {
                            "match": True,
                            "sensitivity": 500
                        }
                    ]
                }
            ]
        )

        self.assertEqual(
                message.sensitivity,
                Sensitivity.PROBLEM,
                "match sensitivity failed")
