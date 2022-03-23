from copy import deepcopy
from django.test import TestCase
from ...core.models.client import Client
from ..models import Account, Organization, OrganizationalUnit, Alias, Position
from .. import msgraph_import_actions

TEST_CORP = [
    {
        "uuid": "37c7aa4e-b884-4f77-9f44-b233237de630",
        "name": "Subgroup to Vejstrand",
        "members": [
            {
                "type": "user",
                "uuid": "118e5d18-90ba-4150-a11c-9162c24bb5ce",
                "givenName": "Charles",
                "surname": "Darwin",
                "userPrincipalName": "Charles@darwindomain.onmicrosoft.com"
            }
        ]
    },
    {
        "uuid": "64116cda-5c3c-4e32-b5a2-01cea0be9888",
        "name": "Casuals Golf Club",
        "members": [
            {
                "type": "user",
                "uuid": "3382c90d-9646-4562-9f47-3994957030a6",
                "givenName": "Albert",
                "surname": "Twostones",
                "userPrincipalName": "albert@darwindomain.onmicrosoft.com"
            },
            {
                "type": "user",
                "uuid": "118e5d18-90ba-4150-a11c-9162c24bb5ce",
                "givenName": "Charles",
                "surname": "Darwin",
                "userPrincipalName": "Charles@darwindomain.onmicrosoft.com"
            },
        ]
    },
    {
        "uuid": "7e6bc04d-15c1-420b-999d-c12581520c23",
        "name": "Vejstrand",
        "members": [
            {
                "type": "user",
                "uuid": "118e5d18-90ba-4150-a11c-9162c24bb5ce",
                "givenName": "Charles",
                "surname": "Darwin",
                "userPrincipalName": "Charles@darwindomain.onmicrosoft.com"
            },
            {
                "type": "group",
                "uuid": "37c7aa4e-b884-4f77-9f44-b233237de630",
                "displayName": "Subgroup to Vejstrand"
            },
            {
                "type": "user",
                "uuid": "93f2f74e-3811-476f-ac56-e7f0d3007fcc",
                "givenName": "Guy",
                "surname": "Average",
                "userPrincipalName": "guy@darwindomain.onmicrosoft.com"
            }
        ]
    }
]


class MSGraphImportTest(TestCase):
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

        # Import from json
        msgraph_import_actions.perform_msgraph_import(
            TEST_CORP, self.org
        )

    def tearDown(self):
        self.org.delete()

    def test_ou_import(self):
        """ Importing should create corresponding OU's from JSON"""
        all_uuids = set()
        for ou in TEST_CORP:
            all_uuids.add(ou["uuid"])

        imported_ids = OrganizationalUnit.objects.values("imported_id")

        for imp_id in imported_ids:
            self.assertIn(imp_id["imported_id"],
                          list(all_uuids),
                          "Not all OU's were created!")

    def test_account_import(self):
        """ Importing should create corresponding account objects """

        all_uuids = set()
        for ou in TEST_CORP:
            for member in ou["members"]:
                if member["type"] == "user":
                    all_uuids.add(member["uuid"])

        imported_ids = Account.objects.values("imported_id")

        for imp_id in imported_ids:
            self.assertIn(imp_id["imported_id"],
                          list(all_uuids),
                          "Not all accounts were created!")

    def test_create_positions(self):
        """ Accounts and connected positions should be created """

        for ou in TEST_CORP:
            ou_uuid = ou["uuid"]
            for member in ou["members"]:
                if member["type"] == "user":
                    ou_obj = OrganizationalUnit.objects.get(imported_id=ou_uuid)
                    acc_obj = Account.objects.get(imported_id=member["uuid"])

                    self.assertTrue(Position.objects.filter(
                        account=acc_obj,
                        unit=ou_obj
                    ).exists(),
                                    "No matching position object!"
                                    )

    def test_create_alias(self):
        for ou in TEST_CORP:
            for member in ou["members"]:
                if member["type"] == "user":
                    member_id = member["uuid"]
                    self.assertTrue(
                        Alias.objects.filter(
                            account__imported_id=member_id
                        ).exists(),
                        "No matching alias object!"
                    )

    def test_delete_user(self):
        # Guy Average is being removed
        UPDATED_CORP = deepcopy(TEST_CORP)
        for ou in UPDATED_CORP:
            for i in range(len(ou["members"])):
                if ou["members"][i]["uuid"] == "93f2f74e-3811-476f-ac56-e7f0d3007fcc":
                    del ou["members"][i]

        # Run import again
        msgraph_import_actions.perform_msgraph_import(
            UPDATED_CORP, self.org
        )
        # Now Guy Average and associated Alias+Position should no longer exist.
        self.assertFalse(
            Account.objects.filter(
                imported_id="93f2f74e-3811-476f-ac56-e7f0d3007fcc").exists(),
            "Account not deleted!"
        )
        self.assertFalse(
            Position.objects.filter(
                account__imported_id="93f2f74e-3811-476f-ac56-e7f0d3007fcc").exists(),
            "Position not deleted!"
        )
        self.assertFalse(
            Alias.objects.filter(
                account__imported_id="93f2f74e-3811-476f-ac56-e7f0d3007fcc").exists(),
            "Alias not deleted!"
        )
        # The OU he belonged to (Vejstrand) should still exist - it has other members
        self.assertTrue(
            OrganizationalUnit.objects.filter(
                name="Vejstrand").exists(),
            "OU shouldn't be deleted in this case!"
        )

    def test_account_attribute_update(self):
        UPDATED_CORP = deepcopy(TEST_CORP)

        # Run import again
        msgraph_import_actions.perform_msgraph_import(
            UPDATED_CORP, self.org
        )

        # Verify he indeed exists after import
        self.assertTrue(
            Account.objects.filter(
                imported_id="93f2f74e-3811-476f-ac56-e7f0d3007fcc",
                first_name="Guy", last_name="Average").exists()
        )

        # Guy Average changes name to Poul Poulsen
        for ou in UPDATED_CORP:
            for i in range(len(ou["members"])):
                if ou["members"][i]["uuid"] == "93f2f74e-3811-476f-ac56-e7f0d3007fcc":
                    ou["members"][i]["givenName"] = "Poul"
                    ou["members"][i]["surname"] = "Poulsen"
                    break

        # Run import again
        msgraph_import_actions.perform_msgraph_import(
            UPDATED_CORP, self.org
        )

        # Verify changed attributes after import
        self.assertTrue(
            Account.objects.filter(
                imported_id="93f2f74e-3811-476f-ac56-e7f0d3007fcc",
                first_name="Poul", last_name="Poulsen").exists()
        )

        # ... and not with the old attributes anymore
        self.assertFalse(
            Account.objects.filter(
                imported_id="93f2f74e-3811-476f-ac56-e7f0d3007fcc",
                first_name="Guy", last_name="Average").exists()
        )
