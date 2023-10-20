from django.test import TestCase
from parameterized import parameterized

from ...core.models.client import Client
from ..models.account import Account
from ..models.organization import Organization, replace_nordics

from ..utils import prepare_and_publish


class ReplaceSpecialCharactersTest(TestCase):
    @parameterized.expand([
        ("tæstcåsø", "t&aelig;stc&aring;s&oslash;"),
        ("Næstved", "N&aelig;stved"),
        ("Torben", "Torben"),
        ("bLaNdInG", "bLaNdInG"),
        ("BlÆnDiNg", "Bl&AElig;nDiNg"),
        ("HÅR", "H&Aring;R"),
        ("SØVAND", "S&Oslash;VAND")
    ])
    def test_nordics_are_replaced(self, input, expected):
        """
        A string containing 'æ', 'ø' and/or 'å' will have those
        instances replaced according to
        https://www.thesauruslex.com/typo/eng/enghtml.htm
        """
        replaced_string = replace_nordics(input)
        self.assertEqual(replaced_string, expected)


class ImportHelperTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.client = Client.objects.create(
                name="Common Client")
        cls.org1 = Organization.objects.create(
                client=cls.client,
                name="Org One")
        cls.org2 = Organization.objects.create(
                client=cls.client,
                name="Org Two")

    def setUp(self):
        self.mikkel = Account.objects.create(
                username="mt@orgone.test",
                first_name="Mikkel", last_name="Testsen",
                organization=self.org1)

    def test_prepare_and_publish_scope(self):
        """Importing a new Account into an Organization does not delete that
        Organization's manually-created Accounts."""

        jens = Account(
                username="jt",
                first_name="Jens", last_name="Testsen",
                organization=self.org1,

                imported=True,
                imported_id="jt@orgone.test")

        prepare_and_publish(
                self.org1,
                {"jt@orgone.test"},
                to_add=[jens],
                to_delete=[],
                to_update=[])

        self.mikkel.refresh_from_db()
        self.assertIsNotNone(
                self.mikkel.pk,
                "manually-created Account was erroneously deleted")

    def test_prepare_and_publish_isolation(self):
        """Importing a new Account into an Organization should have no effect
        on other Organizations."""

        jens = Account(
                username="jt",
                first_name="Jens", last_name="Testsen",
                organization=self.org2,

                imported=True,
                imported_id="jt@orgtwo.test")

        prepare_and_publish(
                self.org2,
                {"jt@orgtwo.test"},
                to_add=[jens],
                to_delete=[],
                to_update=[])

        self.mikkel.refresh_from_db()
        self.assertIsNotNone(
                self.mikkel.pk,
                "manually-created Account was erroneously deleted")
