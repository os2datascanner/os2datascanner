import json

from django.test import TestCase

from ..reportapp.management.commands.event_collector import handle_clean_message
from ..reportapp.utils import create_alias_and_match_relations
from ..organizations.models import Account, Alias, Organization, AliasType
from ..reportapp.models.documentreport import DocumentReport

# This is a real raw_matches field from test data. This could probably be done
# in a better way.
raw_matches_json_matched = json.loads('''
{
  "handle": {
    "path": "Flere sider.html",
    "type": "lo-object",
    "source": {
      "type": "lo",
      "handle": {
        "path": "/Flere sider.docx",
        "type": "web",
        "source": {
          "url": "http://nginx",
          "type": "web",
          "exclude": [],
          "sitemap": null
        },
        "referrer": {
          "path": "/",
          "type": "web",
          "source": {
            "url": "http://nginx",
            "type": "web",
            "exclude": [],
            "sitemap": null
          },
          "last_modified": null
        },
        "last_modified": null
      }
    }
  },
  "origin": "os2ds_matches",
  "matched": true,
  "matches": [
    {
      "rule": {
        "name": "CPR regel",
        "type": "cpr",
        "blacklist": [
          "tullstatistik",
          "fakturanummer",
          "p-nummer",
          "p-nr",
          "fak-nr",
          "customer-no",
          "p.nr",
          "faknr",
          "customer no",
          "dhk:tx",
          "bilagsnummer",
          "test report no",
          "tullstatistisk",
          "ordrenummer",
          "pnr",
          "protocol no.",
          "order number"
        ],
        "whitelist": [
          "cpr"
        ],
        "modulus_11": true,
        "sensitivity": 1000,
        "ignore_irrelevant": true
      },
      "matches": [
        {
          "match": "1111XXXXXX",
          "offset": 1,
          "context": "XXXXXX-XXXX XXXXXX-XXXX XXXXXX-XXXX XXXXXX-XXXX",
          "probability": 1.0,
          "sensitivity": 1000,
          "context_offset": 1
        },
        {
          "match": "1111XXXXXX",
          "offset": 22,
          "context": "XXXXXX-XXXX XXXXXX-XXXX XXXXXX-XXXX XXXXXX-XXXX XXXXXX-XXXX",
          "probability": 1.0,
          "sensitivity": 1000,
          "context_offset": 22
        },
        {
          "match": "1111XXXXXX",
          "offset": 33,
          "context": "XXXXXX-XXXX XXXXXX-XXXX XXXXXX-XXXX XXXXXX-XXXX XXXXXX-XXXX",
          "probability": 1.0,
          "sensitivity": 1000,
          "context_offset": 33
        },
        {
          "match": "1111XXXXXX",
          "offset": 48,
          "context": "XXXXXX-XXXX XXXXXX-XXXX XXXXXX-XXXX XXXXXX-XXXX XXXXXX-XXXX",
          "probability": 1.0,
          "sensitivity": 1000,
          "context_offset": 48
        },
        {
          "match": "1111XXXXXX",
          "offset": 63,
          "context": "XXXXXX-XXXX XXXXXX-XXXX XXXXXX-XXXX XXXXXX-XXXX",
          "probability": 1.0,
          "sensitivity": 1000,
          "context_offset": 50
        }
      ]
    }
  ],
  "scan_spec": {
    "rule": {
      "name": "CPR regel",
      "type": "cpr",
      "blacklist": [
        "tullstatistik",
        "fakturanummer",
        "p-nummer",
        "p-nr",
        "fak-nr",
        "customer-no",
        "p.nr",
        "faknr",
        "customer no",
        "dhk:tx",
        "bilagsnummer",
        "test report no",
        "tullstatistisk",
        "ordrenummer",
        "pnr",
        "protocol no.",
        "order number"
      ],
      "whitelist": [
        "cpr"
      ],
      "modulus_11": true,
      "sensitivity": 1000,
      "ignore_irrelevant": true
    },
    "source": {
      "type": "lo",
      "handle": {
        "path": "/Flere sider.docx",
        "type": "web",
        "source": {
          "url": "http://nginx",
          "type": "web",
          "exclude": [],
          "sitemap": null
        },
        "referrer": {
          "path": "/",
          "type": "web",
          "source": {
            "url": "http://nginx",
            "type": "web",
            "exclude": [],
            "sitemap": null
          },
          "last_modified": null
        },
        "last_modified": null
      }
    },
    "progress": null,
    "scan_tag": {
      "time": "2023-01-05T11:32:26+01:00",
      "user": "dev",
      "scanner": {
        "pk": 2,
        "name": "Local nginx",
        "test": false
      },
      "destination": "pipeline_collector",
      "organisation": {
        "name": "OS2datascanner",
        "uuid": "0e18b3f2-89b6-4200-96cd-38021bbfa00f"
      }
    },
    "filter_rule": null,
    "configuration": {
      "skip_mime_types": [
        "image/*"
      ]
    }
  }
}
''')


class HandleCleanMessageTest(TestCase):

    def setUp(self):
        org = Organization.objects.create(name="TestOrg")
        self.bøffen = Account.objects.create(
            username="Bøffen", organization=org)
        self.egon = Account.objects.create(
            username="egon", organization=org)
        for i in range(10):
            DocumentReport.objects.create(
                name=f"Report-{i}",
                owner="bøffen",
                scanner_job_pk=1,
                path=f"report-{i}-1-bøffen",
                raw_matches=raw_matches_json_matched)
        for i in range(10):
            DocumentReport.objects.create(
                name=f"Report-{i}",
                owner="egon olsen",
                scanner_job_pk=1,
                path=f"report-{i}-1-egon",
                raw_matches=raw_matches_json_matched)
        for i in range(10):
            DocumentReport.objects.create(
                name=f"Report-{i}",
                owner="bøffen",
                scanner_job_pk=2,
                path=f"report-{i}-2-bøffen",
                raw_matches=raw_matches_json_matched)
        for i in range(10):
            DocumentReport.objects.create(
                name=f"Report-{i}",
                owner="egon olsen",
                scanner_job_pk=2,
                path=f"report-{i}-2-egon",
                raw_matches=raw_matches_json_matched)
        bøffen_alias = Alias.objects.create(
            account=self.bøffen,
            user=self.bøffen.user,
            _alias_type=AliasType.GENERIC,
            _value="bøffen")
        egon_alias = Alias.objects.create(
            account=self.egon,
            user=self.egon.user,
            _alias_type=AliasType.GENERIC,
            _value="egon olsen")

        create_alias_and_match_relations(bøffen_alias)
        create_alias_and_match_relations(egon_alias)

    def test_cleaning_document_reports_single_account_and_scanner(self):
        """Giving a CleanMessage to the event_message_received_raw-function
        should delete all DocumentReport-objects associated with the given
        account and scanner."""

        message = {
            "scanners_accounts_dict": {
              1: {
                "uuids": [self.bøffen.uuid],
                "usernames": [self.bøffen.username]
              }
            },
            "type": "clean_document_reports"}

        handle_clean_message(message)

        self.assertEqual(DocumentReport.objects.count(), 30)
        self.assertEqual(
            DocumentReport.objects.filter(
                alias_relation__account=self.bøffen,
                scanner_job_pk=1).count(),
            0)
        self.assertEqual(
            DocumentReport.objects.filter(
                alias_relation__account=self.bøffen,
                ).exclude(scanner_job_pk=1).count(),
            10)
        self.assertEqual(
            DocumentReport.objects.filter(
                alias_relation__account=self.egon).count(),
            20)

    def test_cleaning_document_reports_with_no_scanners(self):
        """Giving a CleanMessage to the event_message_received_raw-function
        without a scanner_job_pk should not delete any DocumentReport-objects."""
        message = {
            "scanners_accounts_dict": {},
            "type": "clean_document_reports"}

        handle_clean_message(message)
        self.assertEqual(DocumentReport.objects.count(), 40)
        self.assertEqual(
            DocumentReport.objects.filter(
                alias_relation__account=self.bøffen).count(),
            20)
        self.assertEqual(
            DocumentReport.objects.filter(
                alias_relation__account=self.egon).count(),
            20)

    def test_cleaning_document_reports_multiple_accounts_single_scanner(self):
        """Giving a CleanMessage to the event_message_received_raw-function
        should delete all DocumentReport-objects associated with the given
        accounts and scanner."""
        message = {
            "scanners_accounts_dict": {
              1: {
                "uuids": [str(self.bøffen.uuid), str(self.egon.uuid)],
                "usernames": [self.bøffen.username, self.egon.username]
              }
            },
            "type": "clean_document_reports"}

        handle_clean_message(message)

        self.assertEqual(DocumentReport.objects.count(), 20)
        self.assertEqual(
            DocumentReport.objects.filter(
                alias_relation__account=self.bøffen,
                scanner_job_pk=1).count(),
            0)
        self.assertEqual(
            DocumentReport.objects.filter(
                alias_relation__account=self.bøffen,
                ).exclude(scanner_job_pk=1).count(),
            10)
        self.assertEqual(
            DocumentReport.objects.filter(
                alias_relation__account=self.egon,
                scanner_job_pk=1).count(),
            0)
        self.assertEqual(
            DocumentReport.objects.filter(
                alias_relation__account=self.egon,
                ).exclude(scanner_job_pk=1).count(),
            10)

    def test_cleaning_document_reports_single_account_multiple_scanners(self):
        """Giving a CleanMessage to the event_message_received_raw-function
        should delete all DocumentReport-objects associated with the given
        account and scanners."""
        message = {
            "scanners_accounts_dict": {
              1: {
                "uuids": [str(self.bøffen.uuid)],
                "usernames": [self.bøffen.username]
              },
              2: {
                "uuids": [str(self.bøffen.uuid)],
                "usernames": [self.bøffen.username]
              }
            },
            "type": "clean_document_reports"}

        handle_clean_message(message)

        self.assertEqual(DocumentReport.objects.count(), 20)
        self.assertEqual(
            DocumentReport.objects.filter(
                alias_relation__account=self.bøffen,
                scanner_job_pk__in=[1, 2]).count(),
            0)
        self.assertEqual(
            DocumentReport.objects.filter(
                alias_relation__account=self.bøffen,
                ).exclude(scanner_job_pk__in=[1, 2]).count(),
            0)
        self.assertEqual(
            DocumentReport.objects.filter(
                alias_relation__account=self.egon,
                ).count(),
            20)

    def test_cleaning_document_reports_multiple_accounts_and_scanners(self):
        """Giving a CleanMessage to the event_message_received_raw-function
        should delete all DocumentReport-objects associated with the given
        accounts and scanners."""
        message = {
            "scanners_accounts_dict": {
              1: {
                "uuids": [str(self.bøffen.uuid), str(self.egon.uuid)],
                "usernames": [self.bøffen.username, self.egon.username]
              },
              2: {
                "uuids": [str(self.bøffen.uuid), str(self.egon.uuid)],
                "usernames": [self.bøffen.username, self.egon.username]
              }
            },
            "type": "clean_document_reports"}

        handle_clean_message(message)

        self.assertEqual(
            DocumentReport.objects.filter(
                alias_relation__account=self.bøffen,
                scanner_job_pk=1).count(),
            0)
        self.assertEqual(
            DocumentReport.objects.filter(
                alias_relation__account=self.bøffen,
                scanner_job_pk=2).count(),
            0)
        self.assertEqual(
            DocumentReport.objects.filter(
                alias_relation__account=self.egon,
                scanner_job_pk=1).count(),
            0)
        self.assertEqual(
            DocumentReport.objects.filter(
                alias_relation__account=self.egon,
                scanner_job_pk=2).count(),
            0)
