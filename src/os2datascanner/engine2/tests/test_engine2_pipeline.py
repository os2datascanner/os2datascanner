import unittest

from os2datascanner.engine2.rules.rule import Sensitivity
from os2datascanner.engine2.rules.dummy import AlwaysMatchesRule
from os2datascanner.engine2.pipeline import messages


class Engine2PipelineTests(unittest.TestCase):
    def test_rule_sensitivity(self):
        message = messages.MatchesMessage(
            scan_spec=None, # unused (at present)
            handle=None, # unused (at present)
            matched=True,
            matches=[
                messages.MatchFragment(
                    rule=AlwaysMatchesRule(sensitivity=Sensitivity.CRITICAL),
                    matches=[
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
                )
            ]
        )

        self.assertEqual(
                message.sensitivity,
                Sensitivity.CRITICAL,
                "rule sensitivity failed")

    def test_match_sensitivity(self):
        message = messages.MatchesMessage(
            scan_spec={}, # unused (at present)
            handle=None, # unused (at present)
            matched=True,
            matches=[
                messages.MatchFragment(
                    rule=AlwaysMatchesRule(sensitivity=Sensitivity.CRITICAL),
                    matches=[
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
                )
            ]
        )

        self.assertEqual(
                message.sensitivity,
                Sensitivity.PROBLEM,
                "match sensitivity failed")

    def test_anomalous_sensitivity(self):
        message = messages.MatchesMessage(
            scan_spec={}, # unused (at present)
            handle=None, # unused (at present)
            matched=True,
            matches=[
                messages.MatchFragment(
                    rule=AlwaysMatchesRule(sensitivity=Sensitivity.NOTICE),
                    matches=[
                        {
                            "match": True,
                            "sensitivity": 1000
                        }
                    ]
                )
            ]
        )

        self.assertEqual(
                message.sensitivity,
                Sensitivity.NOTICE,
                "sensitivity too high")
