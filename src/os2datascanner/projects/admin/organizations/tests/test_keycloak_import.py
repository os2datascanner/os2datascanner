from copy import deepcopy
from unittest import TestCase

from ...core.models.client import Client
from ..models import Account, Organization, OrganizationalUnit
from .. import keycloak_actions


TEST_CORP = [
    {
        "id": "4f533264-6174-6173-6361-6e6e65720000",
        "username": "ted@test.invalid",
        "firstName": "Ted",
        "lastName": "Testsen",
        "attributes": {
            "LDAP_ENTRY_DN": [
                "CN=Ted Testsen,OU=Testers,O=Test Corp."
            ],
            "memberOf": [
                "CN=Group 2,O=Test Corp."
            ]
        }
    },
    {
        "id": "4f533264-6174-6173-6361-6e6e65720001",
        "username": "todd@test.invalid",
        "firstName": "Todd",
        "lastName": "Testsen",
        "attributes": {
            "LDAP_ENTRY_DN": [
                "CN=Todd Testsen,OU=Testers,O=Test Corp."
            ],
            "memberOf": [
                "CN=Group 1,O=Test Corp.",
                "CN=Group A,O=Test Corp."
            ]
        }
    },
    {
        "id": "4f533264-6174-6173-6361-6e6e65720002",
        "username": "thad@test.invalid",
        "firstName": "Thad",
        "lastName": "Testsen",
        "attributes": {
            "LDAP_ENTRY_DN": [
                "CN=Thad Testsen,OU=Testers,O=Test Corp."
            ],
            "memberOf": [
                "CN=Group A,O=Test Corp."
            ]
        }
    }
]


class KeycloakImportTest(TestCase):
    dummy_client = None

    @classmethod
    def setUpClass(cls):
        cls.dummy_client = Client.objects.create(
                name="OS2datascanner test dummy_client")


    @classmethod
    def tearDownClass(cls):
        cls.dummy_client.delete()
 
    def setUp(self):
        self.org = Organization.objects.create(
                name="Test Corp.",
                client=self.dummy_client)

    def tearDown(self):
        self.org.delete()

    def test_ou_import(self):
        """It should be possible to import users into a LDAP OU-based hierarchy
        from Keycloak's JSON output."""
        keycloak_actions.perform_import_raw(
                self.org, TEST_CORP,
                keycloak_actions.keycloak_dn_selector)

        for tester in TEST_CORP:
            account = Account.objects.get(uuid=tester["id"])
            self.assertEqual(
                    tester["username"],
                    account.username,
                    "user import failure")

    def test_group_import(self):
        """It should be possible to import users into a group-based hierarchy
        from Keycloak's JSON output."""
        keycloak_actions.perform_import_raw(
                self.org, TEST_CORP,
                keycloak_actions.keycloak_group_dn_selector)

        for tester in TEST_CORP:
            account = Account.objects.get(uuid=tester["id"])
            self.assertEqual(
                    tester["username"],
                    account.username,
                    "username incorrectly imported")

            for group in tester.get("attributes", {}).get("memberOf", []):
                self.assertTrue(
                        account.units.filter(imported_id=group).exists(),
                        "user not in group")

    def test_removal(self):
        """Removing a user from Keycloak's JSON output should also remove that
        user from the database."""
        self.test_ou_import()

        thads = list(Account.objects.filter(first_name="Thad"))

        keycloak_actions.perform_import_raw(
                self.org, [
                        tester
                        for tester in TEST_CORP
                        if tester.get("firstName") != "Thad"],
                keycloak_actions.keycloak_dn_selector)

        for thad in thads:
            with self.assertRaises(Account.DoesNotExist,
                    msg="user still present after deletion"):
                thad.refresh_from_db()

    def test_group_change_ou(self):
        """Changing the LDAP DN of a user in a group-based hierarchy should
        change their properties without affecting their positions."""
        self.test_group_import()

        todds = list(Account.objects.filter(first_name="Todd"))

        NEW_CORP = deepcopy(TEST_CORP)
        for tester in NEW_CORP:
            if tester["firstName"] == "Todd":
                tester["attributes"]["LDAP_ENTRY_DN"] = [
                        f"CN=Todd {tester['lastName']},"
                        "OU=Experimenters,O=Test Corp."]

        keycloak_actions.perform_import_raw(
                self.org, NEW_CORP,
                keycloak_actions.keycloak_group_dn_selector)

        for todd in todds:
            todd.refresh_from_db()
            self.assertIn(
                    "OU=Experimenters",
                    todd.imported_id,
                    "DN did not change")

    def test_change_group(self):
        """It should be possible to move a user from one group to another."""
        self.test_group_import()

        teds = list(Account.objects.filter(first_name="Ted"))

        for ted in teds:
            ted.units.get(imported_id="CN=Group 2,O=Test Corp.")
            with self.assertRaises(OrganizationalUnit.DoesNotExist,
                    msg="user in new group before move"):
                ted.units.get(imported_id="CN=Group 1,O=Test Corp.")

        NEW_CORP = deepcopy(TEST_CORP)
        for tester in NEW_CORP:
            if tester["firstName"] == "Ted":
                tester["attributes"]["memberOf"] = [
                    "CN=Group 1,O=Test Corp."
                ]

        keycloak_actions.perform_import_raw(
                self.org, NEW_CORP,
                keycloak_actions.keycloak_group_dn_selector)

        for ted in teds:
            ted.refresh_from_db()
            ted.units.get(imported_id="CN=Group 1,O=Test Corp.")
            with self.assertRaises(OrganizationalUnit.DoesNotExist,
                    msg="user in old group after move"):
                ted.units.get(imported_id="CN=Group 2,O=Test Corp.")

    def test_remove_ou(self):
        """Removing every user from a group or organisational unit should
        remove its representation in the database."""
        self.test_group_import()

        OrganizationalUnit.objects.get(imported_id="CN=Group 2,O=Test Corp.")

        NEW_CORP = deepcopy(TEST_CORP)
        for tester in NEW_CORP:
            try:
                tester["attributes"]["memberOf"].remove(
                        "CN=Group 2,O=Test Corp.")
            except ValueError:
                pass

        keycloak_actions.perform_import_raw(
                self.org, NEW_CORP,
                keycloak_actions.keycloak_group_dn_selector)

        with self.assertRaises(OrganizationalUnit.DoesNotExist,
                msg="defunct OU not removed"):
            OrganizationalUnit.objects.get(
                    imported_id="CN=Group 2,O=Test Corp.")
