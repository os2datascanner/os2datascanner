import json

from django.test import TestCase
from django.utils.text import slugify

from os2datascanner.projects.admin.core.models.client import Client
from os2datascanner.projects.admin.organizations.models.organization import Organization
from os2datascanner.engine2.rules.rule import Rule
from ..adminapp.models.rules.regexrule import RegexRule, RegexPattern
from ..adminapp.models.apikey import APIKey


class APITest(TestCase):
    def setUp(self):
        client1 = Client.objects.create(name="client1")
        self.org1 = Organization.objects.create(
                name="General Services Corp.",
                uuid="b560361d-2b1f-4174-bb03-55e8b693ad0c",
                slug=slugify("General Services Corp."),
                client=client1,
        )
        client2 = Client.objects.create(name="client2")
        self.org2 = Organization.objects.create(
                name="Ministry of Tasks",
                uuid="a3575dec-8d92-4266-a8d1-97b7b84817c0",
                slug=slugify("Ministry of Tasks"),
                client=client2,
        )

        self.rule1 = RegexRule.objects.create(
                organization=self.org1, name="Check for tax number")
        RegexPattern.objects.create(
                regex=self.rule1, pattern_string="[0-9]{12}")
        self.rule2 = RegexRule.objects.create(
                organization=self.org2, name="Check for department ID")
        RegexPattern.objects.create(
                regex=self.rule2, pattern_string="Dx[1-58]{4}")

        self.key1_bad = APIKey.objects.create(organization=self.org1)
        self.key1_good = APIKey.objects.create(
                organization=self.org1, scope="get-rule/1")
        self.key2 = APIKey.objects.create(
                organization=self.org2, scope="get-rule/1")

    def test_api_success(self):
        """Making a valid API call with the appropriate authorised key should
        succeed and return the right object."""
        for rule, key in (
                (self.rule1, self.key1_good), (self.rule2, self.key2),):
            r = self.client.post(
                    "/api/get-rule/1",
                    {"rule_id": rule.pk},
                    "application/json",
                    HTTP_AUTHORIZATION="Bearer {0}".format(key.uuid))
            self.assertEqual(r.status_code, 200,
                             "API request failed")
            body = json.loads(r.content.decode("ascii"))
            self.assertEqual(
                    Rule.from_json_object(body["rule"]),
                    rule.make_engine2_rule(),
                    "returned rule not equal")

    def test_api_no_key(self):
        """Making a valid API call with no key should fail with HTTP 401
        Unauthorized."""
        r = self.client.post(
                "/api/get-rule/1",
                {"rule_id": self.rule1.pk}, "application/json")
        self.assertEqual(
                r.status_code, 401,
                "API request did not fail as expected")

    def test_api_invalid_header(self):
        """Making a valid API call with an invalid HTTP header should fail with
        HTTP 400 Bad Request."""
        r = self.client.post(
                "/api/get-rule/1",
                {"rule_id": self.rule1.pk}, "application/json",
                HTTP_AUTHORIZATION="Invalid INVALID")
        self.assertEqual(
                r.status_code, 400,
                "API request did not fail as expected")

    def test_api_invalid_key(self):
        """Making a valid API call with an invalid key should fail with HTTP
        401 Unauthorized."""
        r = self.client.post(
                "/api/get-rule/1",
                {"rule_id": self.rule1.pk}, "application/json",
                HTTP_AUTHORIZATION="Bearer INVALID")
        self.assertEqual(
                r.status_code, 401,
                "API request did not fail as expected")

    def test_api_wrong_key(self):
        """Making a valid API call with a valid key for the wrong organisation
        should fail as though the object did not exist."""
        r = self.client.post(
                "/api/get-rule/1",
                {"rule_id": self.rule1.pk}, "application/json",
                HTTP_AUTHORIZATION="Bearer {0}".format(self.key2.uuid))
        self.assertEqual(
                r.status_code, 200,
                "API request failed")
        body = json.loads(r.content.decode("ascii"))
        self.assertEqual(
                body["status"], "fail",
                "API key granted access to another organisation")

    def test_api_unauthorised(self):
        """Making an API call with a valid key whose scope does not cover that
        API call should fail with HTTP 403 Forbidden."""
        r = self.client.post(
                "/api/get-scanner/1",
                HTTP_AUTHORIZATION="Bearer {0}".format(self.key1_good.uuid))
        self.assertEqual(
                r.status_code, 403,
                "API request failed")
