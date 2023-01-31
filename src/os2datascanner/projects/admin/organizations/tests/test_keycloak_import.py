from copy import deepcopy
from django.test import TestCase
from ...core.models.client import Client
from ..models import Account, Organization, OrganizationalUnit, Alias, Position
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
    },
    {
        "id": "4f533264-6174-6173-6361-6e6e65720003",
        "username": "root@test.invalid",
        "attributes": {
            "LDAP_ENTRY_DN": [
                "CN=root,OU=Testers,O=Test Corp."
            ],
            "memberOf": [
                "CN=Group A,O=Test Corp."
            ]
        }
    },
    {
        "attributes": {
            "LDAP_ENTRY_DN": [
                "CN=secret_backdoor,OU=Testers,O=Test Corp."
            ],
            "memberOf": [
                "CN=Group A,O=Test Corp."
            ]
        }
    },
]

TEST_CORP_TWO = [
    {
        "id": "4f533264-6174-6173-6361-6e6e65720010",
        "username": "ursula@test.invalid",
        "firstName": "Ursula",
        "lastName": "Testsen",
        "email": "ursulas@brevdue.dk",
        "attributes": {
            "LDAP_ENTRY_DN": [
                "CN=Ursula Testsen,OU=TheUCorp,O=Test Corp."
            ],
            "memberOf": [
                "CN=Group 1,O=Test Corp.",
                "CN=Group 2,O=Test Corp."
            ]
        }
    },
    {
        "id": "4f533264-6174-6173-6361-6e6e65720011",
        "username": "ulrich@test.invalid",
        "firstName": "Ulrich",
        "lastName": "Testsen",
        "email": "ulrichs@brevdue.dk",
        "attributes": {
            "LDAP_ENTRY_DN": [
                "CN=Ulrich Testsen,OU=TheUCorp,O=Test Corp."
            ],
            "memberOf": [
                "CN=Group 1,O=Test Corp.",
                "CN=Group 2,O=Test Corp."
            ]
        }
    },

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
            if "id" not in tester:
                continue
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
            if "id" not in tester:
                continue
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
            if tester.get("firstName") == "Todd":
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
            if tester.get("firstName") == "Ted":
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

    def test_import_user_in_multiple_groups_should_only_get_one_email_alias(self):
        """ A user can be a memberOf multiple groups, but it is still only one
        user, and should result in only one email-alias (given that the user
        has an email attribute)"""
        keycloak_actions.perform_import_raw(
            self.org, TEST_CORP_TWO,
            keycloak_actions.keycloak_group_dn_selector)

        ursula_aliases = Alias.objects.filter(_value="ursulas@brevdue.dk")

        self.assertEqual(ursula_aliases.count(), 1,
                         msg="Either duplicate or no email aliases for user created")

    def test_delete_user_relation_to_group(self):
        keycloak_actions.perform_import_raw(
            self.org, TEST_CORP_TWO,
            keycloak_actions.keycloak_group_dn_selector)

        ursula = TEST_CORP_TWO[0]
        account = Account.objects.get(uuid=ursula["id"])

        self.assertEqual(Position.objects.filter(account=account).count(), 2,
                         msg="Position not correctly created")

        NEW_CORP = deepcopy(TEST_CORP_TWO)
        # Now only member of one group instead of two.
        NEW_CORP[0]["attributes"]["memberOf"] = ["CN=Group 2,O=Test Corp."]

        # Import again
        keycloak_actions.perform_import_raw(
            self.org, NEW_CORP,
            keycloak_actions.keycloak_group_dn_selector)

        self.assertEqual(Position.objects.filter(account=account).count(), 1,
                         msg="Position not updated correctly")

        # The OU should still exist though, as there is still a user with a
        # connection to it.
        self.assertTrue(
                OrganizationalUnit.objects.filter(
                        imported_id="CN=Group 1,O=Test Corp.").exists(),
                msg="OU doesn't exist but should")

        # Delete Ulrich from the TEST_CORP_TWO
        del NEW_CORP[1]

        # Import again
        keycloak_actions.perform_import_raw(
            self.org, NEW_CORP,
            keycloak_actions.keycloak_group_dn_selector)

        # The OU should now not exist as there is no user with a connection to
        # it.
        self.assertFalse(
                OrganizationalUnit.objects.filter(
                        imported_id="CN=Group 1,O=Test Corp.").exists(),
                msg="OU is not deleted")

    def test_property_update(self):
        """Changing a user's name should update the corresponding properties in
        the database."""
        self.test_ou_import()

        for user in Account.objects.filter(organization=self.org):
            self.assertNotEqual(
                    user.first_name,
                    "Tadeusz",
                    "premature or invalid property update(?)")

        NEW_CORP = deepcopy(TEST_CORP)
        for tester in NEW_CORP:
            try:
                # The hero of the Polish epic poem Pan Tadeusz, since you ask
                # (the first line of which is "O Lithuania, my homeland!")
                tester["firstName"] = "Tadeusz"
                tester["lastName"] = "Soplica"
            except ValueError:
                pass

        keycloak_actions.perform_import_raw(
                self.org, NEW_CORP,
                keycloak_actions.keycloak_group_dn_selector)

        for user in Account.objects.filter(organization=self.org):
            self.assertEqual(
                    (user.first_name, user.last_name),
                    ("Tadeusz", "Soplica"),
                    "property update failed")
