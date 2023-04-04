from django.test import TestCase

from ...adminapp.models.scannerjobs.scanner import Scanner
from ...organizations.models import Organization, OrganizationalUnit, Account
from ..utils import construct_dict_from_scanners_stale_accounts


class PostImportCleanupTests(TestCase):

    def setUp(self):
        org = Organization.objects.first()
        self.scanner = Scanner.objects.create(name="Scammer, I mean Scanner", organization=org)

        oluf = Account.objects.create(username="Oluf", organization=org)
        gertrud = Account.objects.create(username="Gertrud", organization=org)
        self.benny = Account.objects.create(username="Benny", organization=org)

        fritz = Account.objects.create(username="Fritz", organization=org)
        günther = Account.objects.create(username="Günther", organization=org)
        hansi = Account.objects.create(username="Hansi", organization=org)

        fam_sand = OrganizationalUnit.objects.create(name="Familien Sand", organization=org)
        nisser = OrganizationalUnit.objects.create(name="Nisserne", organization=org)

        fam_sand.account_set.add(oluf, gertrud)
        nisser.account_set.add(fritz, günther, hansi)

        self.scanner.covered_accounts.add(oluf, gertrud, self.benny, fritz, günther, hansi)

        self.scanner.org_unit.add(fam_sand, nisser)

    def test_construct_dict_from_scanners_stale_accounts_one_stale_account(self):
        """When calling the 'construct_dict_from_scanners_stale_accounts' while
        one account is no longer in the org_units covered by the scanner, but
        is still in the covered_accounts-field of the scanner, the function
        should return a dict with that scanner and that account."""
        # Benny is in the covered_accounts field of the scanner, but not in
        # any org_unit covered by the scanner, so we expect:
        expected_out = {
            self.scanner.pk: {
                "uuids": [str(self.benny.uuid)],
                "usernames": [self.benny.username]
            }
        }

        real_out = construct_dict_from_scanners_stale_accounts()

        self.assertEqual(real_out, expected_out)

    def test_construct_dict_with_synced_scanner(self):
        """When calling the 'construct_dict_from_scanners_stale_accounts' right
        after syncing the covered accounts of a scanner, the function should
        return an empty dict."""

        self.scanner.sync_covered_accounts()

        scanners_accounts_dict = construct_dict_from_scanners_stale_accounts()

        self.assertEqual(scanners_accounts_dict, {})
