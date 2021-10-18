import unittest
from datetime import datetime, timezone

from os2datascanner.engine2.rules.address import AddressRule
from os2datascanner.engine2.rules.cpr import CPRRule
from os2datascanner.engine2.rules.dimensions import DimensionsRule
from os2datascanner.engine2.rules.last_modified import LastModifiedRule
from os2datascanner.engine2.rules.logical import (
    OrRule,
    AndRule,
    NotRule,
    AllRule,
    oxford_comma,
)
from os2datascanner.engine2.rules.name import NameRule
from os2datascanner.engine2.rules.regex import RegexRule
from os2datascanner.engine2.rules.rule import Sensitivity


class RuleTests(unittest.TestCase):
    def test_simplerule_matches(self):
        candidates = [
            (
                CPRRule(modulus_11=False, ignore_irrelevant=False),
                """
2205995008: forbryder,
230500 0003: forbryder,
240501-0006: forbryder,
250501-1987: forbryder""",
                ["2205XXXXXX", "2305XXXXXX", "2405XXXXXX", "2505XXXXXX"],
            ),
            (
                CPRRule(modulus_11=True, ignore_irrelevant=True),
                """
2205995008: forbryder,
230500 0003: forbryder,
240501-0006: forbryder,
250501-1987: forbryder""",
                ["2205XXXXXX", "2305XXXXXX", "2405XXXXXX"],
            ),
            (
                CPRRule(
                    modulus_11=True, ignore_irrelevant=True, examine_context=False
                ),
                """
Vejstrand Kommune, Børn- og Ungeforvaltningen. P-nr. 2205995008
Vejstrand Kommune, Børn- og Ungeforvaltningen. P-nummer: 2305000003
240501-0006""",
                ["2205XXXXXX", "2305XXXXXX", "2405XXXXXX"],
            ),
            (
                CPRRule(
                    modulus_11=True, ignore_irrelevant=True, examine_context=True,
                    blacklist=[],
                ),
                """
Vejstrand Kommune, Børn- og Ungeforvaltningen. P-nr. 2205995008
Vejstrand Kommune, Børn- og Ungeforvaltningen. P-nummer: 2305000003
240501-0006""",
                ["2205XXXXXX", "2305XXXXXX", "2405XXXXXX"],
            ),
            (
                CPRRule(
                    modulus_11=True, ignore_irrelevant=True, examine_context=True,
                ),
                """
Vejstrand Kommune, Børn- og Ungeforvaltningen. P-nr. 2205995008
Vejstrand Kommune, Børn- og Ungeforvaltningen. P-nummer: 2305000003
240501-0006""",
                [],
            ),
            (
                CPRRule(
                    modulus_11=True, ignore_irrelevant=True, examine_context=True,
                    whitelist=["whiteword"]
                ),
                """
Vejstrand Kommune, Børn- og Ungeforvaltningen. WhiteWord 2205995008
Vejstrand Kommune, Børn- og Ungeforvaltningen. NotAcceptedCase 2305000003
Vejstrand Kommune, 240501-0006""",
                ["2205XXXXXX", "2405XXXXXX"],
            ),
            (
                RegexRule("((four|six)( [aopt]+)?|(one|seven) [aopt]+)"),
                """
one
one potato
two potato
three potato
four
five potato
six potato
seven potato
more!""",
                ["one potato", "four", "six potato", "seven potato"],
            ),
            (
                LastModifiedRule(
                    datetime(2019, 12, 24, 23, 59, 59, tzinfo=timezone.utc)
                ),
                datetime(2019, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
                ["2019-12-31T23:59:59+0000"],
            ),
            (
                LastModifiedRule(
                    datetime(2019, 12, 24, 23, 59, 59, tzinfo=timezone.utc)
                ),
                datetime(2019, 5, 22, 0, 0, 1, tzinfo=timezone.utc),
                None,
            ),
            (
                DimensionsRule(
                    width_range=range(0, 16385),
                    height_range=range(0, 16385),
                    min_dim=256,
                ),
                (128, 256),
                [[128, 256]],
            ),
            (
                DimensionsRule(
                    width_range=range(0, 16385),
                    height_range=range(0, 16385),
                    min_dim=256,
                ),
                (128, 255),
                [],
            ),
            (
                DimensionsRule(
                    width_range=range(256, 1024),
                    height_range=range(256, 1024),
                    min_dim=0,
                ),
                (256, 256),
                [[256, 256]],
            ),
            (
                DimensionsRule(
                    width_range=range(256, 1024),
                    height_range=range(256, 1024),
                    min_dim=0,
                ),
                (32, 32),
                [],
            ),
        ]

        for rule, in_value, expected in candidates:
            with self.subTest(rule):
                json = rule.to_json_object()
                back_again = rule.from_json_object(json)
                self.assertEqual(rule, back_again)

            with self.subTest(rule):
                matches = rule.match(in_value)
                if expected:
                    self.assertEqual([match["match"] for match in matches], expected)
                else:
                    self.assertFalse(list(matches))

    compound_candidates = [
        (
            AndRule(RegexRule("A"), OrRule(RegexRule("B"), RegexRule("C"))),
            [
                ("A", False, 3),
                ("AB", True, 2),
                ("ABC", True, 2),
                ("BC", False, 1),
                ("AC", True, 3),
            ],
        ),
        (
            NotRule(AndRule(RegexRule("A"), OrRule(RegexRule("B"), RegexRule("C")))),
            [
                ("A", True, 3),
                ("AB", False, 2),
                ("ABC", False, 2),
                ("BC", True, 1),
                ("AC", False, 3),
            ],
        ),
        (
            AndRule(NotRule(OrRule(RegexRule("B"), RegexRule("C"))), RegexRule("A")),
            [
                ("A", True, 3),
                ("AB", False, 1),
                ("ABC", False, 1),
                ("BC", False, 1),
                ("AC", False, 2),
            ],
        ),
        (
            AndRule(AllRule(RegexRule("A"), RegexRule("B")), RegexRule("C")),
            [
                ("A", False, 3),
                ("AB", False, 3),
                ("ABC", True, 3),
                ("BC", True, 3),
                ("AC", True, 3),
                ("C", False, 2),
            ],
        ),
    ]

    def test_compound_rule_matches(self):
        for rule, tests in RuleTests.compound_candidates:
            for input_string, outcome, evaluation_count in tests:
                now = rule
                evaluations = 0

                while True:
                    print(f"evaluating rule {now}")
                    head, pve, nve = now.split()
                    evaluations += 1
                    match = list(head.match(input_string))
                    print(f"{head} had the matches {match}")
                    if match:
                        now = pve
                    else:
                        now = nve
                    if isinstance(now, bool):
                        break
                print(f"conclusion: input: {input_string}; result: {now}; "
                      f"expected: {outcome}; evaluations: {evaluations}")
                self.assertEqual(
                    outcome, now, "{0}: wrong result".format(input_string)
                )
                self.assertEqual(
                    evaluation_count,
                    evaluations,
                    "{0}: wrong evaluation count".format(input_string),
                )

    def test_json_round_trip(self):
        for rule, _ in RuleTests.compound_candidates:
            with self.subTest(rule):
                json = rule.to_json_object()
                back_again = rule.from_json_object(json)
                self.assertEqual(rule, back_again)

    def test_oxford_comma(self):
        self.assertEqual(oxford_comma(["Monday"], "and"), "Monday")
        self.assertEqual(
            oxford_comma(["Monday", "Tuesday"], "and"), "Monday and Tuesday"
        )
        self.assertEqual(
            oxford_comma(["Monday", "Tuesday", "Wednesday"], "and"),
            "Monday, Tuesday, and Wednesday",
        )

    def test_rule_names(self):
        A = RegexRule("A", name="Fragment A")
        B = RegexRule("B", name="Fragment B")
        C1 = RegexRule("C1", name="Fragment C1")
        C2 = RegexRule("C2", name="Fragment C2")
        C = OrRule(C1, C2, name="Fragment C")
        self.assertEqual(AndRule(A, B).presentation, "(Fragment A and Fragment B)")
        self.assertEqual(
            OrRule(A, B, C).presentation, "(Fragment A, Fragment B, or Fragment C)"
        )

    def test_json_backwards_compatibility(self):
        with self.subTest("old CPR rule"):
            self.assertEqual(
                    CPRRule.from_json_object({
                        "type": "cpr"
                    }),
                    CPRRule(),
                    "deserialisation of old CPR rule failed")

    def test_name_address_rule_matches(self):
        candidates = [
            (
                # sensitivity is for standalone matches
                NameRule(whitelist=["Joakim"], blacklist=["Malkeko"],
                         sensitivity=Sensitivity.INFORMATION.value),
                (
                    "Anders\n"           # match standalone name.
                    "Anders and\n"       # match standalone name
                    "Anders      And\n"  # match full name. Only first name in namelist
                    "Anders And\n"       # match full name
                    "A. And\n"           # match regex, but not in namelist -> not returned
                    "J.-V And\n"         # -"-
                    "J-V. And\n"         # -"-
                    "J.V. And\n"         # -"-
                    "J.v. And\n"         # Does not match regex
                    "Joakim And\n"       # match regex and namelist, but in whitelist
                    "Andrea V. And\n"    # First name in namelist
                    "Joakim Nielsen\n"   # last name in namelist and not whitelisted.
                    "Anders Andersine Mickey Per Nielsen\n"
                    # match full name
                    "Nora Malkeko\n"     # In blacklist
                ),
                [    # expected matches
                    ["Anders", Sensitivity.INFORMATION.value],
                    ["Anders", Sensitivity.INFORMATION.value],
                    ["Anders And", Sensitivity.PROBLEM.value],
                    ["Anders      And", Sensitivity.PROBLEM.value],
                    ["Joakim Nielsen", Sensitivity.PROBLEM.value],
                    ["Andrea V. And", Sensitivity.PROBLEM.value],
                    ["Anders Andersine Mickey Per Nielsen",
                     Sensitivity.CRITICAL.value],
                    ["Nora Malkeko", Sensitivity.CRITICAL.value],
                ]
            ),
            (
                # user supplied sensitivity is not used
                AddressRule(whitelist=["Tagensvej"], blacklist=["PilÆstræde"]),
                (
                    "H.C. Andersens Boul 15, 2. 0006, 1553 København V, Danmark\n"
                    "H.C. Andersens Boul, 1553 Kbh. V\n"
                    "10. Februar Vej 75\n"                    # unusual names from the list
                    "400-Rtalik\n"
                    "H/F Solpl-Lærkevej\n"
                    "H. H. Hansens Vej\n"
                    "H H Kochs Vej\n"
                    "Øer I Isefjord 15\n"                     # does unicode work?
                    "Tagensvej 15\n"                          # whitelisted
                    "der er en bygning på PilÆstræde, men\n"  # not in address list/blacklisted
                    "Magenta APS, PilÆstræde 43,  3. sal, 1112 København\n"
                ),
                [
                    ["H.C. Andersens Boul 15, 2. 0006, 1553 København V",
                     Sensitivity.CRITICAL.value],
                    ["H.C. Andersens Boul, 1553 Kbh. V", Sensitivity.PROBLEM.value],
                    ["10. Februar Vej 75", Sensitivity.CRITICAL.value],
                    ["400-Rtalik", Sensitivity.PROBLEM.value],
                    ["H/F Solpl-Lærkevej", Sensitivity.PROBLEM.value],
                    ["H. H. Hansens Vej", Sensitivity.PROBLEM.value],
                    ["H H Kochs Vej", Sensitivity.PROBLEM.value],
                    ["Øer I Isefjord 15", Sensitivity.CRITICAL.value],
                    ["PilÆstræde", Sensitivity.CRITICAL.value],
                    ["PilÆstræde 43,  3. sal, 1112 København", Sensitivity.CRITICAL.value],
                ]
            ),
        ]

        for rule, in_value, expected in candidates:
            with self.subTest(rule):
                json = rule.to_json_object()
                back_again = rule.from_json_object(json)
                self.assertEqual(rule, back_again)

            with self.subTest(rule):
                matches = rule.match(in_value)
                # matches ARE NOT returned in order. They are stored as a set
                self.assertCountEqual(
                    [[match["match"], match['sensitivity']] for match in matches],
                    expected)
