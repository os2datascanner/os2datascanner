from django.test import TestCase

from ..models import OrganizationalUnit, Organization, Account
from ...adminapp.models.scannerjobs.scanner import Scanner


class AccountMethodTests(TestCase):

    def setUp(self):
        # Select existing org
        org = Organization.objects.first()

        # Create objects
        self.unit1 = OrganizationalUnit.objects.create(
            name="Unit1", organization=org)
        self.unit2 = OrganizationalUnit.objects.create(
            name="Unit2", organization=org)
        self.scanner1 = Scanner.objects.create(
            name="Hansi & Günther", organization=org)
        self.scanner2 = Scanner.objects.create(
            name="Hansi", organization=org)
        self.hansi = Account.objects.create(username="Hansi", organization=org)
        self.günther = Account.objects.create(username="Günther", organization=org)
        self.fritz = Account.objects.create(username="Fritz", organization=org)

        # Assign accounts to a unit
        self.unit1.account_set.add(self.hansi, self.günther)
        self.unit2.account_set.add(self.hansi)

    def test_get_stale_scanners(self):
        """Make sure, that accounts can correctly identify, when they have
        been dropped from a scanner."""

        # Hansi and Günther are both assigned to scanner1. Only Hansi is
        # assigned to scanner2. Both are added to 'covered_accounts' of both
        # scanners. Fritz is not covered in any way.
        self.scanner1.org_unit.add(self.unit1)
        self.scanner2.org_unit.add(self.unit2)
        self.scanner1.covered_accounts.add(self.hansi, self.günther)
        self.scanner2.covered_accounts.add(self.hansi, self.günther)

        # Hansi has not been dropped, and should get an empty queryset here.
        hansi_dropped = self.hansi.get_stale_scanners()
        # Günther has been dropped from scanner2, and should see that here.
        günther_dropped = self.günther.get_stale_scanners()
        # Fritz has not been dropped, and should get an empty queryset here.
        fritz_dropped = self.fritz.get_stale_scanners()

        self.assertFalse(hansi_dropped.exists())
        self.assertFalse(fritz_dropped.exists())
        self.assertTrue(günther_dropped.exists())
        self.assertEqual(günther_dropped.count(), 1)
        self.assertEqual(günther_dropped.first(), self.scanner2)
