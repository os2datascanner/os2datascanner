import datetime
import json

from django.test import TestCase
from django.utils import timezone

from ..models import Account, Organization, Alias
from ..models.account import StatusChoices
from ...reportapp.models.documentreport import DocumentReport


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


def make_matched_document_reports_for(alias, handled=0, amount=10, created=timezone.now()):
    for i in range(amount):
        dr = DocumentReport.objects.create(raw_matches=raw_matches_json_matched)
        dr.created_timestamp = created
        if i < handled:
            dr.resolution_status = 0
        dr.save()
        dr.alias_relation.add(alias)


class AccountTest(TestCase):

    def setUp(self) -> None:
        olsenbanden = Organization.objects.create(name='Olsenbanden')

        self.egon_acc = Account.objects.create(username='egon', organization=olsenbanden)
        self.benny_acc = Account.objects.create(username='benny', organization=olsenbanden)
        self.kjeld_acc = Account.objects.create(username='kjeld', organization=olsenbanden)

        # Aliases, so the accounts can have documentreports associated
        self.egon_alias = Alias.objects.create(
            user=self.egon_acc.user,
            account=self.egon_acc,
            _alias_type="email",
            _value="egon@olsenbanden.com")
        self.benny_alias = Alias.objects.create(
            user=self.benny_acc.user,
            account=self.benny_acc,
            _alias_type="SID",
            _value="this_is_a_SID")
        self.kjeld_alias = Alias.objects.create(
            user=self.kjeld_acc.user,
            account=self.kjeld_acc,
            _alias_type="generic")

    def test_save_with_no_new_matches_and_some_handled(self):
        """If a user has not recently had new matches, their status should be
        'OK'."""

        handled_matches = 6
        all_matches = 10

        # Make documentreport that are > 3 weeks old.
        make_matched_document_reports_for(
            self.egon_alias,
            handled=handled_matches,
            amount=all_matches,
            created=timezone.now() -
            datetime.timedelta(
                days=100))

        # This is the real test. This is where .match_count and .match_status are set.
        self.egon_acc.save()

        self.assertEqual(
            self.egon_acc.match_count,
            all_matches-handled_matches,
            f"Expected to find {all_matches-handled_matches} unhandled match, "
            f"but found {self.egon_acc.match_count} instead.")
        self.assertEqual(
            self.egon_acc.match_status,
            StatusChoices.OK,
            f"Expected match_status to be 'OK', but found "
            f"{self.egon_acc.match_status.label} instead.")

    def test_save_with_some_new_matches_and_some_handled(self):
        """If a user has not handled at least 75% of their matches the past
        3 weeks, their status should be 'BAD', otherwise it should be 'OK'.
        If the user has no matches at all, their status should be 'GOOD'."""

        # Egon has no unhandled matches at all.
        egon_handled = 10
        egon_all = 10
        make_matched_document_reports_for(self.egon_alias, handled=egon_handled, amount=egon_all)

        # Benny has handled 80% of his matches the past 3 weeks.
        benny_handled = 8
        benny_all = 10
        make_matched_document_reports_for(self.benny_alias, handled=benny_handled, amount=benny_all)

        # Kjeld has only handled 60%.
        kjeld_handled = 6
        kjeld_all = 10
        make_matched_document_reports_for(self.kjeld_alias, handled=kjeld_handled, amount=kjeld_all)

        # This is where the match_status and match_count are set.
        self.egon_acc.save()
        self.benny_acc.save()
        self.kjeld_acc.save()

        self.assertEqual(egon_all-egon_handled, self.egon_acc.match_count)
        self.assertEqual(
            StatusChoices.GOOD,
            self.egon_acc.match_status,
            f"Expected match_status to be 'GOOD', but found "
            f"{self.egon_acc.match_status.label} instead.")
        self.assertEqual(benny_all-benny_handled, self.benny_acc.match_count)
        self.assertEqual(
            StatusChoices.OK,
            self.benny_acc.match_status,
            f"Expected match_status to be 'OK', but found "
            f"{self.egon_acc.match_status.label} instead.")
        self.assertEqual(kjeld_all-kjeld_handled, self.kjeld_acc.match_count)
        self.assertEqual(
            StatusChoices.BAD,
            self.kjeld_acc.match_status,
            f"Expected match_status to be 'BAD', but found "
            f"{self.egon_acc.match_status.label} instead.")

    def test_save_with_some_new_matches_and_no_handled(self):
        """If a user has some new matches, and handled none, their status
        should be 'BAD'"""

        # Kjeld has not done anything.
        handled = 0
        all_matches = 10
        make_matched_document_reports_for(self.kjeld_alias, handled=handled, amount=all_matches)

        self.kjeld_acc.save()

        self.assertEqual(all_matches-handled, self.kjeld_acc.match_count)
        self.assertEqual(
            StatusChoices.BAD,
            self.kjeld_acc.match_status,
            f"Expected match_status to be 'BAD', but found "
            f"{self.egon_acc.match_status.label} instead.")

    def test_save_with_no_new_matches_and_no_handled(self):
        """If a user has not handled any matches, their status should be 'BAD',
        even if none of their matches are new."""

        # Benny has not done anything
        handled = 0
        all_matches = 10
        make_matched_document_reports_for(
            self.benny_alias,
            handled=handled,
            amount=all_matches,
            created=timezone.now() -
            datetime.timedelta(
                days=100))

        self.benny_acc.save()

        self.assertEqual(all_matches-handled, self.benny_acc.match_count)
        self.assertEqual(
            StatusChoices.BAD,
            self.benny_acc.match_status,
            f"Expected match_status to be 'BAD', but found "
            f"{self.egon_acc.match_status.label} instead.")

    def test_count_matches_by_week_format(self):
        """The count_matches_by_week-method should return a list of dicts with
        the following structure:
        [
            {
                "weeknum": <int>,
                "matches": <int>,
                "new": <int>,
                "handled": <int>
            },
            { ... }
        ]
        """

        egon_weekly_matches = self.egon_acc.count_matches_by_week(weeks=10)
        kjeld_weekly_matches = self.kjeld_acc.count_matches_by_week(weeks=104)
        # When no number of weeks are specified, the default is 52.
        benny_weekly_matches = self.benny_acc.count_matches_by_week()

        self.assertEqual(len(egon_weekly_matches), 10)
        self.assertEqual(len(kjeld_weekly_matches), 104)
        self.assertEqual(len(benny_weekly_matches), 52)

        self.assertIn("weeknum", egon_weekly_matches[0].keys())
        self.assertIn("matches", egon_weekly_matches[0].keys())
        self.assertIn("new", egon_weekly_matches[0].keys())
        self.assertIn("handled", egon_weekly_matches[0].keys())

    def test_account_count_matches_by_week_created_none(self):
        """Test the Account.count_matches_by_week-method with a report without
        a created timestamp, to make sure the method does not break."""
        make_matched_document_reports_for(self.kjeld_alias, handled=0, amount=1, created=None)
        kjeld_weekly_matches = self.kjeld_acc.count_matches_by_week(weeks=1)

        self.assertEqual(kjeld_weekly_matches[0]["matches"], 1)

    def test_account_count_matches_from_ten_to_one_to_zero(self):
        all_matches = 10
        handled = 0
        make_matched_document_reports_for(self.kjeld_alias, handled=handled, amount=all_matches)

        # Refresh match count.
        self.kjeld_acc._count_matches()
        # Assert
        self.assertEqual(self.kjeld_acc.match_count, all_matches,
                         "Incorrect match_count on account object!")

        # Handle 9/10

        DocumentReport.objects.filter(alias_relation=self.kjeld_alias).update(resolution_status=0)
        dr = DocumentReport.objects.filter(alias_relation=self.kjeld_alias).first()
        dr.resolution_status = None
        dr.save()
        # Refresh match count
        self.kjeld_acc._count_matches()
        # Assert
        self.assertEqual(self.kjeld_acc.match_count, 1,
                         "Incorrect match_count on account object! All but one should be handled.")

        # Handle all matches
        DocumentReport.objects.filter(alias_relation=self.kjeld_alias).update(resolution_status=0)
        # Refresh match count
        self.kjeld_acc._count_matches()
        # Assert
        self.assertEqual(self.kjeld_acc.match_count, 0,
                         "Incorrect match_count on account object! All should be handled.")

    def test_account_withheld_matches_from_ten_to_one_to_zero(self):
        all_matches = 10
        handled = 0
        make_matched_document_reports_for(self.kjeld_alias, handled=handled, amount=all_matches)

        # Mark Kjeld's matches as withheld
        DocumentReport.objects.filter(alias_relation=self.kjeld_alias).update(
            only_notify_superadmin=True)

        # Refresh count
        self.kjeld_acc._count_matches()
        # Assert
        self.assertEqual(self.kjeld_acc.withheld_matches, 10,
                         "Matches that should be withheld aren't counted as withheld!")
        self.assertEqual(self.kjeld_acc.match_count, 0,
                         "Match count is not updated!")

        # Distribute 9 of  Kjeld's matches
        DocumentReport.objects.filter(alias_relation=self.kjeld_alias).update(
            only_notify_superadmin=False)
        dr = DocumentReport.objects.filter(alias_relation=self.kjeld_alias).first()
        dr.only_notify_superadmin = True
        dr.save()

        # Refresh count
        self.kjeld_acc._count_matches()
        # Assert
        self.assertEqual(self.kjeld_acc.withheld_matches, 1,
                         "Matches that shouldn't be withheld are counted as withheld!")
        self.assertEqual(self.kjeld_acc.match_count, 9,
                         "Match count is not updated!")

        # Distribute last one
        DocumentReport.objects.filter(alias_relation=self.kjeld_alias,
                                      only_notify_superadmin=True).update(
            only_notify_superadmin=False)
        # Refresh count
        self.kjeld_acc._count_matches()
        # Assert, nothing should be withheld
        self.assertEqual(self.kjeld_acc.withheld_matches, 0,
                         "Matches that shouldn't be withheld are counted as withheld!")
        self.assertEqual(self.kjeld_acc.match_count, 10,
                         "Match count is not updated!")
