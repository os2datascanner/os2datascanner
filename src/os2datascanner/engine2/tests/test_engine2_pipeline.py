import json
import unittest

from os2datascanner.engine2.model import msgraph  # only for testing censoring
from os2datascanner.engine2.rules.rule import Sensitivity
from os2datascanner.engine2.rules.dummy import AlwaysMatchesRule
from os2datascanner.engine2.pipeline import messages, exporter


class Engine2PipelineTests(unittest.TestCase):
    def test_rule_sensitivity(self):
        message = messages.MatchesMessage(
            scan_spec=None,  # unused (at present)
            handle=None,  # unused (at present)
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
            scan_spec={},  # unused (at present)
            handle=None,  # unused (at present)
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
            scan_spec={},  # unused (at present)
            handle=None,  # unused (at present)
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

    def test_exporter_censoring(self):
        secret_source = msgraph.MSGraphMailSource(
                # Randomly-generated UUIDs
                "995c7bff-022b-45b3-b43f-a87877d5b051",
                "1864a889-df0d-4b96-a438-92871096e089",
                client_secret="SECRETVALUE")
        secret_handle = msgraph.MSGraphMailAccountHandle(
                secret_source, "t.estsen@placeholder.invalid")

        dummy_scan_spec = messages.ScanSpecMessage(
                scan_tag=messages.ScanTagFragment.make_dummy(),
                source=secret_source,
                rule=AlwaysMatchesRule(),
                configuration={},
                filter_rule=None,
                progress=None)

        for message in (
                messages.MatchesMessage(
                    scan_spec=dummy_scan_spec,
                    handle=secret_handle,
                    matched=True,
                    matches=[
                        messages.MatchFragment(
                                rule=AlwaysMatchesRule(),
                                matches=[{"content": True}])
                    ],
                ),
                messages.MetadataMessage(
                    scan_tag=dummy_scan_spec.scan_tag,
                    handle=secret_handle,
                    metadata={"email-account": "t.estsen@placeholder.invalid"}
                ),
                messages.ProblemMessage(
                    scan_tag=dummy_scan_spec.scan_tag,
                    handle=secret_handle,
                    source=None,
                    message="fatal: Expected picture of dog, but found cat"
                )):
            with self.subTest():
                uncensored_json = json.dumps(message.to_json_object())
                censored_json = json.dumps(
                        exporter.censor_outgoing_message(
                                message).to_json_object())
                self.assertIn(
                        "SECRETVALUE",
                        uncensored_json,
                        "client secret not present in JSON output(?)")
                self.assertNotIn(
                        "SECRETVALUE",
                        censored_json,
                        "client secret present in censored JSON output")
