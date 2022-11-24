from django.test import TestCase

from ..adminapp.models.rules.rule import Sensitivity
from ..adminapp.models.rules.regexrule import RegexRule, RegexPattern
from ..adminapp.models.rules.customrule import CustomRule


class RuleTest(TestCase):
    def test_regexrule_translation(self):
        names = ("Jason", "Timothy", "Davina", "Kristi",)

        r = RegexRule.objects.create(
                name="Look for names",
                sensitivity=Sensitivity.CRITICAL)
        for name in names:
            RegexPattern.objects.create(regex=r, pattern_string=name)

        e2r = r.make_engine2_rule()

        self.assertEqual(
                e2r._name,
                r.name,
                "names do not match")

        self.assertEqual(
                e2r._sensitivity.value,
                1000,
                "sensitivities do not match")

        for name in names:
            self.assertNotEqual(
                    list(e2r.match(name)),
                    [],
                    f"generated rule could not find {name}")

    def test_customrule_translation(self):
        document = """\
From the desk of Kristjan Evil
TO: David Jensen

We must make sure that Jens Davidsen doesn't find out about the plan. Do
everything in your power to keep it a secret!

The first steps will be taken on Tuesday. Mwahahahaha ha ha ha ha.

Yours in nastiness
Kristjan Evil
"""
        r = CustomRule.objects.create(
                name="Look for names",
                _rule={
                    "type": "name",
                    "expansive": False,
                    "whitelist": [],
                    "blacklist": [],
                    "sensitivity": 1000
                },
                sensitivity=Sensitivity.LOW)

        e2r = r.make_engine2_rule()

        self.assertEqual(
                e2r._name,
                r.name,
                "names do not match")

        self.assertEqual(
                e2r._sensitivity.value,
                1000,
                "higher engine2 sensitivity was ignored")

        self.assertEqual(
                {m["match"] for m in e2r.match(document)},
                {"Kristjan Evil", "David Jensen",
                 "Jens Davidsen", "Kristjan Evil"},
                "expected names not found")
