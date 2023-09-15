from django.test import TestCase
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from ..models import Organization, OrganizationalUnit, Account, Position
from ...core.models import Client, Administrator

from os2datascanner.core_organizational_structure.models.organization import (
    StatisticsPageConfigChoices, DPOContactChoices, SupportContactChoices)


class OrganizationListViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="name", password="secret")
        self.client.force_login(self.user)
        self.client1 = Client.objects.create(name="Client1")
        self.client2 = Client.objects.create(name="Client2")

    def test_superuser_list(self):
        """Superusers should be able to see all clients."""
        self.user.is_superuser = True
        self.user.save()

        url = reverse_lazy("organization-list")

        response = self.client.get(url)

        self.assertIn(self.client1, response.context.get("client_list"),
                      msg="Client not correctly shown to superuser")
        self.assertIn(self.client2, response.context.get("client_list"),
                      msg="Client not correctly shown to superuser")

    def test_administrator_for_list(self):
        """Administrators should only be able to see the client, that they are
        administrator for."""
        Administrator.objects.create(user=self.user, client=self.client1)

        url = reverse_lazy("organization-list")

        response = self.client.get(url)

        self.assertIn(self.client1, response.context.get("client_list"),
                      msg="Client not correctly shown to superuser")
        self.assertNotIn(self.client2, response.context.get("client_list"),
                         msg="Client wrongly shown to user!")

    def test_regular_user_list(self):
        """A user which is neither Administrator or superuser should not be
        able to see anything."""

        url = reverse_lazy("organization-list")

        response = self.client.get(url)

        self.assertNotIn(self.client1, response.context.get("client_list"),
                         msg="Client wrongly shown to user!")
        self.assertNotIn(self.client2, response.context.get("client_list"),
                         msg="Client wrongly shown to user!")


class AddOrganizationViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='name', password='secret')
        self.client.force_login(self.user)
        self.mock_client = Client.objects.create(name='mock_client')

    def test_superuser_create_unique_name_organization(self):
        """Successfully creating an organization redirects to the list view."""
        self.user.is_superuser = True
        self.user.save()
        num_org_pre = Organization.objects.count()
        url = reverse_lazy('add-organization-for',
                           kwargs={'client_id': self.mock_client.uuid})
        response = self.client.post(url, {
            'name': 'Unique',
            'contact_email': 'test@unique.mail',
            'contact_phone': '12341234',
        })

        success_url = reverse_lazy('organization-list')
        num_org_post = Organization.objects.count()
        new_org = Organization.objects.exclude(name="OS2datascanner").first()
        expected_code = 302

        self.assertEqual(
            response.status_code,
            expected_code,
            f"Wrong status code! Received {response.status_code}, but expected {expected_code}.")
        self.assertRedirects(response, success_url)
        self.assertEqual(
            num_org_post,
            num_org_pre + 1,
            f"Wrong number of Organization objects! Found {num_org_post},"
            f" but expected {num_org_pre+1}.")
        self.assertEqual(new_org.name, "Unique",
                         "Name of Organization not set correctly during creation.")
        self.assertEqual(new_org.contact_email, "test@unique.mail",
                         "Contact email of Organization not set correctly during creation.")
        self.assertEqual(new_org.contact_phone, "12341234",
                         "Phone number of Organization not set correctly during creation.")
        self.assertEqual(new_org.client, self.mock_client)

    def test_superuser_create_same_name_organization(self):
        """Providing a name already in use for an organization
        should invalidate the form and display an error."""
        self.user.is_superuser = True
        self.user.save()
        Organization.objects.create(name='Same', slug='same', client=self.mock_client)
        num_org_pre = Organization.objects.count()
        url = reverse_lazy('add-organization-for', kwargs={'client_id': self.mock_client.uuid})
        response = self.client.post(url, {
            'name': 'Same',
            'contact_email': '',
            'contact_phone': '',
        })

        num_org_post = Organization.objects.count()
        expected_code = 200

        self.assertEqual(
            response.status_code,
            expected_code,
            f"Wrong status code! Received {response.status_code}, but expected {expected_code}.")
        self.assertFormError(response, 'form', 'name', _('That name is already taken.'))
        self.assertEqual(
            num_org_post,
            num_org_pre,
            f"Wrong number of Organization objects! Found {num_org_post},"
            f" but expected {num_org_pre}.")

    def test_blank_user_create_organization(self):
        """A user with no permission should not be able to create a new organization."""
        num_org_pre = Organization.objects.count()
        url = reverse_lazy('add-organization-for',
                           kwargs={'client_id': self.mock_client.uuid})
        response = self.client.post(url, {
            'name': 'New Org',
            'contact_email': 'test@unique.mail',
            'contact_phone': '12341234',
        })

        num_org_post = Organization.objects.count()
        expected_code = 403

        self.assertEqual(
            response.status_code,
            expected_code,
            f"Wrong status code! Received {response.status_code}, but expected {expected_code}.")
        self.assertEqual(
            num_org_post,
            num_org_pre,
            f"Wrong number of Organization objects! Found {num_org_post},"
            f" but expected {num_org_pre}.")
        self.assertFalse(Organization.objects.filter(name="New Org").exists(),
                         "Blank user is able to create an organization for a client!")

    def test_administrator_create_organization_not_permitted(self):
        """An administrator for one client should not be able to create a new
        organization for another client."""
        num_org_pre = Organization.objects.count()
        other_client = Client.objects.create(name="other client")
        Administrator.objects.create(user=self.user, client=other_client)
        url = reverse_lazy('add-organization-for',
                           kwargs={'client_id': self.mock_client.uuid})
        response = self.client.post(url, {
            'name': 'New Org',
            'contact_email': 'test@unique.mail',
            'contact_phone': '12341234',
        })

        num_org_post = Organization.objects.count()
        expected_code = 403

        self.assertEqual(
            response.status_code,
            expected_code,
            f"Wrong status code! Received {response.status_code}, but expected {expected_code}.")
        self.assertEqual(
            num_org_post,
            num_org_pre,
            f"Wrong number of Organization objects! Found {num_org_post},"
            f" but expected {num_org_pre}.")
        self.assertFalse(Organization.objects.filter(name="New Org").exists(),
                         "Administrator for wrong client is able to create an "
                         "organization for a client!")

    def test_administrator_create_organization_permitted(self):
        """An administrator for a client should be able to create a new
        organization for that client."""
        num_org_pre = Organization.objects.count()
        Administrator.objects.create(user=self.user, client=self.mock_client)
        url = reverse_lazy('add-organization-for',
                           kwargs={'client_id': self.mock_client.uuid})
        response = self.client.post(url, {
            'name': 'New Org',
            'contact_email': 'test@unique.mail',
            'contact_phone': '12341234',
        })

        success_url = reverse_lazy('organization-list')
        num_org_post = Organization.objects.count()
        new_org = Organization.objects.exclude(name="OS2datascanner").first()
        expected_code = 302

        self.assertEqual(
            response.status_code,
            expected_code,
            f"Wrong status code! Received {response.status_code}, but expected {expected_code}.")
        self.assertRedirects(response, success_url)
        self.assertEqual(
            num_org_post,
            num_org_pre + 1,
            f"Wrong number of Organization objects! Found {num_org_post},"
            f" but expected {num_org_pre+1}.")
        self.assertEqual(new_org.name, "New Org",
                         "Name of Organization not set correctly during creation.")
        self.assertEqual(new_org.contact_email, "test@unique.mail",
                         "Contact email of Organization not set correctly during creation.")
        self.assertEqual(new_org.contact_phone, "12341234",
                         "Phone number of Organization not set correctly during creation.")
        self.assertEqual(new_org.client, self.mock_client)


class UpdateOrganizationViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='name', password='secret')
        self.client.force_login(self.user)
        self.mock_client = Client.objects.create(name='mock_client')
        self.mock_organization = Organization.objects.create(
            name='mock_org', slug='mock_org', client=self.mock_client)

    def test_blank_user_updating_an_organization(self):
        """Users with no permissions should not be able to update any
        organizations."""
        url = reverse_lazy('edit-organization', kwargs={'slug': self.mock_organization.slug})
        response = self.client.post(url, {
            'name': 'Updated Organization',
            'contact_email': 'something@else.com',
            'contact_phone': 'new phone, who dis?',
        })

        updated_org = Organization.objects.exclude(name="OS2datascanner").first()
        expected_code = 404

        self.assertEqual(
            response.status_code,
            expected_code,
            f"Wrong status code! Received {response.status_code}, but expected {expected_code}.")
        self.assertEqual(
            updated_org.name,
            "mock_org",
            "User with no permissions is able to edit organization!")

    def test_administrator_updating_an_organization_permitted(self):
        """An administrator should be able to edit an organization owned by
        the client, that the user is administrator for."""
        Administrator.objects.create(user=self.user, client=self.mock_client)
        num_org_pre = Organization.objects.count()
        url = reverse_lazy('edit-organization', kwargs={'slug': self.mock_organization.slug})
        response = self.client.post(url, {
            'name': 'Updated Organization',
            'contact_email': 'something@else.com',
            'contact_phone': 'new phone, who dis?',
            'leadertab_access': StatisticsPageConfigChoices.MANAGERS,
            'dpotab_access': StatisticsPageConfigChoices.DPOS,
            'show_support_button': False,
            'support_contact_style': SupportContactChoices.NONE,
            'support_name': 'IT',
            'support_value': '',
            'dpo_contact_style': DPOContactChoices.NONE,
            'dpo_name': '',
            'dpo_value': '',
        })

        success_url = reverse_lazy('organization-list')
        num_org_post = Organization.objects.count()
        updated_org = Organization.objects.exclude(name="OS2datascanner").first()
        expected_code = 302

        self.assertEqual(
            response.status_code,
            expected_code,
            f"Wrong status code! Received {response.status_code}, but expected {expected_code}.")
        self.assertRedirects(response, success_url)
        self.assertEqual(
            num_org_post,
            num_org_pre,
            f"Wrong number of Organization objects! Found {num_org_post},"
            f" but expected {num_org_pre}.")
        self.assertEqual(updated_org.name, "Updated Organization",
                         "Name of organization not updated correctly!")
        self.assertEqual(updated_org.contact_email, "something@else.com",
                         "Contact email of organization not updated correctly!")
        self.assertEqual(updated_org.contact_phone, "new phone, who dis?",
                         "Phone number of organization not updated correctly!")
        self.assertEqual(updated_org.client, self.mock_client)

    def test_administrator_updating_an_organization_not_permitted(self):
        """An administrator should not be able to edit an organization owned by
        another client, than the one the user is administrator for."""
        other_client = Client.objects.create(name='other client')
        Administrator.objects.create(user=self.user, client=other_client)
        url = reverse_lazy('edit-organization', kwargs={'slug': self.mock_organization.slug})
        response = self.client.post(url, {
            'name': 'Updated Organization',
            'contact_email': 'something@else.com',
            'contact_phone': 'new phone, who dis?',
        })

        updated_org = Organization.objects.exclude(name="OS2datascanner").first()
        expected_code = 404

        self.assertEqual(
            response.status_code,
            expected_code,
            f"Wrong status code! Received {response.status_code}, but expected {expected_code}.")
        self.assertEqual(
            updated_org.name,
            "mock_org",
            "Administrator for wrong client is able to edit organization!")

    def test_superuser_updating_an_organization(self):
        """Superusers should be able to update all organizations."""
        self.user.is_superuser = True
        self.user.save()
        num_org_pre = Organization.objects.count()
        url = reverse_lazy('edit-organization', kwargs={'slug': self.mock_organization.slug})
        response = self.client.post(url, {
            'name': 'Updated Organization',
            'contact_email': 'something@else.com',
            'contact_phone': 'new phone, who dis?',
            'leadertab_access': StatisticsPageConfigChoices.MANAGERS,
            'dpotab_access': StatisticsPageConfigChoices.DPOS,
            'show_support_button': False,
            'support_contact_style': SupportContactChoices.NONE,
            'support_name': 'IT',
            'support_value': '',
            'dpo_contact_style': DPOContactChoices.NONE,
            'dpo_name': '',
            'dpo_value': '',
        })

        success_url = reverse_lazy('organization-list')
        num_org_post = Organization.objects.count()
        updated_org = Organization.objects.exclude(name="OS2datascanner").first()
        expected_code = 302

        self.assertEqual(
            response.status_code,
            expected_code,
            f"Wrong status code! Received {response.status_code}, but expected {expected_code}.")
        self.assertRedirects(response, success_url)
        self.assertEqual(
            num_org_post,
            num_org_pre,
            f"Wrong number of Organization objects! Found {num_org_post},"
            f" but expected {num_org_pre}.")
        self.assertEqual(updated_org.name, "Updated Organization",
                         "Name of organization not updated correctly!")
        self.assertEqual(updated_org.contact_email, "something@else.com",
                         "Contact email of organization not updated correctly!")
        self.assertEqual(updated_org.contact_phone, "new phone, who dis?",
                         "Phone number of organization not updated correctly!")
        self.assertEqual(updated_org.client, self.mock_client)


class DeleteOrganizationViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='name', password='secret')
        self.client.force_login(self.user)
        self.mock_client = Client.objects.create(name='mock_client')
        self.mock_organization = Organization.objects.create(
            name='mock_org', slug='mock_org', client=self.mock_client)

    def test_blank_user_delete_organization(self):
        """Trying to delete an organization as a user with no permissions at
        all should fail."""
        num_org_pre = Organization.objects.count()
        url = reverse_lazy('delete-organization', kwargs={'slug': self.mock_organization.slug})
        response = self.client.post(url)

        num_org_post = Organization.objects.count()
        expected_code = 403

        self.assertEqual(
            response.status_code,
            expected_code,
            f"Wrong status code! Received {response.status_code}, but expected {expected_code}.")
        self.assertEqual(
            num_org_post,
            num_org_pre,
            f"Wrong number of Organization objects! Found {num_org_post},"
            f" but expected {num_org_pre}.")

    def test_administrator_delete_organization(self):
        """Trying to delete an organization as an administrator for the client
        should fail."""
        num_org_pre = Organization.objects.count()
        Administrator.objects.create(user=self.user, client=self.mock_client)
        url = reverse_lazy('delete-organization', kwargs={'slug': self.mock_organization.slug})
        response = self.client.post(url)

        num_org_post = Organization.objects.count()
        expected_code = 403

        self.assertEqual(
            response.status_code,
            expected_code,
            f"Wrong status code! Received {response.status_code}, but expected {expected_code}.")
        self.assertEqual(
            num_org_post,
            num_org_pre,
            f"Wrong number of Organization objects! Found {num_org_post},"
            f" but expected {num_org_pre}.")

    def test_superuser_delete_organization(self):
        """Trying to delete an organization as a superuser should succeed."""
        self.user.is_superuser = True
        self.user.save()
        num_org_pre = Organization.objects.count()
        url = reverse_lazy('delete-organization', kwargs={'slug': self.mock_organization.slug})
        response = self.client.post(url)

        success_url = reverse_lazy('organization-list')
        num_org_post = Organization.objects.count()
        expected_code = 302

        self.assertEqual(
            response.status_code,
            expected_code,
            f"Wrong status code! Received {response.status_code}, but expected {expected_code}.")
        self.assertRedirects(response, success_url)
        self.assertEqual(
            num_org_post,
            num_org_pre-1,
            f"Wrong number of Organization objects! Found {num_org_post},"
            f" but expected {num_org_pre-1}.")
        self.assertFalse(Organization.objects.filter(name='mock_org').exists())


class OrganizationalUnitListViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="name", password="secret")
        self.client.force_login(self.user)
        self.client1 = Client.objects.create(name="Client1")
        self.client2 = Client.objects.create(name="Client2")

        self.org1 = Organization.objects.create(
            name="Organization1", slug="org1", client=self.client1)
        self.org2 = Organization.objects.create(
            name="Organization2", slug="org2", client=self.client2)

        self.unit1 = OrganizationalUnit.objects.create(name="OrgUnit1", organization=self.org1)
        self.unit2 = OrganizationalUnit.objects.create(name="OrgUnit2", organization=self.org1)
        self.unit3 = OrganizationalUnit.objects.create(name="OrgUnit3", organization=self.org2)
        self.unit4 = OrganizationalUnit.objects.create(name="OrgUnit4", organization=self.org2)

        self.egon = Account.objects.create(username="Egon", organization=self.org1)
        self.benny = Account.objects.create(username="Benny", organization=self.org1)
        self.kjeld = Account.objects.create(username="Kjeld", organization=self.org2)

        self.egon.units.add(self.unit1)
        self.benny.units.add(self.unit2)
        self.kjeld.units.add(self.unit3)

    def test_superuser_list(self):
        """Superusers should be able to see all organizational units."""
        self.user.is_superuser = True
        self.user.save()

        # URL to all units from organization 1
        url1 = reverse_lazy("orgunit-list", kwargs={'org_slug': self.org1.slug})
        # URL to all units from organization 2
        url2 = reverse_lazy("orgunit-list", kwargs={'org_slug': self.org2.slug})

        # This response should yield two units
        response1 = self.client.get(url1)
        # This response should yield one unit, as the other one has no accounts associated
        response2 = self.client.get(url2)
        # This response should yield two units, including one empty
        response3 = self.client.get(url2, {"show_empty": "on"})

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response3.status_code, 200)
        self.assertIn(self.unit1, response1.context.get("object_list"))
        self.assertIn(self.unit2, response1.context.get("object_list"))
        self.assertIn(self.unit3, response2.context.get("object_list"))
        self.assertNotIn(self.unit4, response2.context.get("object_list"))
        self.assertIn(self.unit3, response3.context.get("object_list"))
        self.assertIn(self.unit4, response3.context.get("object_list"))

    def test_administrator_for_list(self):
        """Administrators should be able to see the units belonging to
        organizations, belonging to clients, for which they are
        administrators."""
        Administrator.objects.create(user=self.user, client=self.client2)

        # URL to all units from organization 1
        url1 = reverse_lazy("orgunit-list", kwargs={'org_slug': self.org1.slug})
        # URL to all units from organization 2
        url2 = reverse_lazy("orgunit-list", kwargs={'org_slug': self.org2.slug})

        # This response should yield two units
        response1 = self.client.get(url1)
        # This response should yield one unit, as the other one has no accounts associated
        response2 = self.client.get(url2)
        # This response should yield two units, including one empty
        response3 = self.client.get(url2, {"show_empty": "on"})

        self.assertEqual(response1.status_code, 404)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response3.status_code, 200)
        self.assertIn(self.unit3, response2.context.get("object_list"))
        self.assertNotIn(self.unit4, response2.context.get("object_list"))
        self.assertIn(self.unit3, response3.context.get("object_list"))
        self.assertIn(self.unit4, response3.context.get("object_list"))

    def test_regular_user_list(self):
        """Users with no priviliges should not be able to see any units."""

        # URL to all units from organization 1
        url1 = reverse_lazy("orgunit-list", kwargs={'org_slug': self.org1.slug})
        # URL to all units from organization 2
        url2 = reverse_lazy("orgunit-list", kwargs={'org_slug': self.org2.slug})

        # This response should yield two units
        response1 = self.client.get(url1)
        # This response should yield one unit, as the other one has no accounts associated
        response2 = self.client.get(url2)
        # This response should yield two units, including one empty
        response3 = self.client.get(url2, {"show_empty": "on"})

        self.assertEqual(response1.status_code, 404)
        self.assertEqual(response2.status_code, 404)
        self.assertEqual(response3.status_code, 404)


class OrganizationalUnitListViewAddRemoveManagersTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="name", password="secret")
        self.client.force_login(self.user)
        self.client1 = Client.objects.create(name="Client1")
        self.client2 = Client.objects.create(name="Client2")

        self.org1 = Organization.objects.create(
            name="Organization1", slug="org1", client=self.client1)
        self.org2 = Organization.objects.create(
            name="Organization2", slug="org2", client=self.client2)

        self.unit1 = OrganizationalUnit.objects.create(name="OrgUnit1", organization=self.org1)
        self.unit2 = OrganizationalUnit.objects.create(name="OrgUnit2", organization=self.org1)
        self.unit3 = OrganizationalUnit.objects.create(name="OrgUnit3", organization=self.org2)
        self.unit4 = OrganizationalUnit.objects.create(name="OrgUnit4", organization=self.org2)

        self.egon = Account.objects.create(username="Egon", organization=self.org1)
        self.benny = Account.objects.create(username="Benny", organization=self.org1)
        self.kjeld = Account.objects.create(username="Kjeld", organization=self.org2)

        self.egon.units.add(self.unit1)
        self.benny.units.add(self.unit2)
        self.kjeld.units.add(self.unit3)

    def test_add_manager_superuser(self):
        """A superuser should be able to add managers."""
        self.user.is_superuser = True
        self.user.save()

        # URL to all units from organization 1
        url1 = reverse_lazy("orgunit-list", kwargs={'org_slug': self.org1.slug})
        # URL to all units from organization 2
        url2 = reverse_lazy("orgunit-list", kwargs={'org_slug': self.org2.slug})

        response1 = self.client.post(
            url1, {"add-manager": self.egon.uuid, "orgunit": self.unit1.pk})
        response2 = self.client.post(
            url2, {"add-manager": self.kjeld.uuid, "orgunit": self.unit3.pk})

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        self.assertTrue(
            Position.objects.filter(
                account=self.egon,
                unit=self.unit1,
                role="manager").exists())
        self.assertTrue(
            Position.objects.filter(
                account=self.kjeld,
                unit=self.unit3,
                role="manager").exists())

    def test_remove_manager_superuser(self):
        """A superuser should be able to remove managers from all units."""
        self.user.is_superuser = True
        self.user.save()

        Position.objects.create(account=self.egon, unit=self.unit1, role="manager")
        Position.objects.create(account=self.kjeld, unit=self.unit3, role="manager")

        # URL to all units from organization 1
        url1 = reverse_lazy("orgunit-list", kwargs={'org_slug': self.org1.slug})
        # URL to all units from organization 2
        url2 = reverse_lazy("orgunit-list", kwargs={'org_slug': self.org2.slug})

        response1 = self.client.post(
            url1, {"rem-manager": self.egon.uuid, "orgunit": self.unit1.pk})
        response2 = self.client.post(
            url2, {"rem-manager": self.kjeld.uuid, "orgunit": self.unit3.pk})

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        self.assertFalse(
            Position.objects.filter(
                account=self.egon,
                unit=self.unit1,
                role="manager").exists())
        self.assertFalse(
            Position.objects.filter(
                account=self.kjeld,
                unit=self.unit3,
                role="manager").exists())

    def test_add_manager_administrator(self):
        """An administrator should be able to add managers to units they are
        administrator for."""
        Administrator.objects.create(user=self.user, client=self.client2)

        # URL to all units from organization 1
        url1 = reverse_lazy("orgunit-list", kwargs={'org_slug': self.org1.slug})
        # URL to all units from organization 2
        url2 = reverse_lazy("orgunit-list", kwargs={'org_slug': self.org2.slug})

        response1 = self.client.post(
            url1, {"add-manager": self.egon.uuid, "orgunit": self.unit1.pk})
        response2 = self.client.post(
            url2, {"add-manager": self.kjeld.uuid, "orgunit": self.unit3.pk})

        self.assertEqual(response1.status_code, 404)
        self.assertEqual(response2.status_code, 200)
        self.assertFalse(
            Position.objects.filter(
                account=self.egon,
                unit=self.unit1,
                role="manager").exists())
        self.assertTrue(
            Position.objects.filter(
                account=self.kjeld,
                unit=self.unit3,
                role="manager").exists())

    def test_remove_manager_administrator(self):
        """An administrator should be able to remove managers from the units
        they are administrators for."""
        Administrator.objects.create(user=self.user, client=self.client2)

        Position.objects.create(account=self.egon, unit=self.unit1, role="manager")
        Position.objects.create(account=self.kjeld, unit=self.unit3, role="manager")

        # URL to all units from organization 1
        url1 = reverse_lazy("orgunit-list", kwargs={'org_slug': self.org1.slug})
        # URL to all units from organization 2
        url2 = reverse_lazy("orgunit-list", kwargs={'org_slug': self.org2.slug})

        response1 = self.client.post(
            url1, {"rem-manager": self.egon.uuid, "orgunit": self.unit1.pk})
        response2 = self.client.post(
            url2, {"rem-manager": self.kjeld.uuid, "orgunit": self.unit3.pk})

        self.assertEqual(response1.status_code, 404)
        self.assertEqual(response2.status_code, 200)
        self.assertTrue(
            Position.objects.filter(
                account=self.egon,
                unit=self.unit1,
                role="manager").exists())
        self.assertFalse(
            Position.objects.filter(
                account=self.kjeld,
                unit=self.unit3,
                role="manager").exists())

    def test_add_manager_regular_user(self):
        """An unprivileged user should not be able to add managers to any
        units."""

        # URL to all units from organization 1
        url1 = reverse_lazy("orgunit-list", kwargs={'org_slug': self.org1.slug})
        # URL to all units from organization 2
        url2 = reverse_lazy("orgunit-list", kwargs={'org_slug': self.org2.slug})

        response1 = self.client.post(
            url1, {"add-manager": self.egon.uuid, "orgunit": self.unit1.pk})
        response2 = self.client.post(
            url2, {"add-manager": self.kjeld.uuid, "orgunit": self.unit3.pk})

        self.assertEqual(response1.status_code, 404)
        self.assertEqual(response2.status_code, 404)
        self.assertFalse(
            Position.objects.filter(
                account=self.egon,
                unit=self.unit1,
                role="manager").exists())
        self.assertFalse(
            Position.objects.filter(
                account=self.kjeld,
                unit=self.unit3,
                role="manager").exists())

    def test_remove_manager_regular_user(self):
        """An unprivileged user should not be able to remove managers from
        any units."""

        Position.objects.create(account=self.egon, unit=self.unit1, role="manager")
        Position.objects.create(account=self.kjeld, unit=self.unit3, role="manager")

        # URL to all units from organization 1
        url1 = reverse_lazy("orgunit-list", kwargs={'org_slug': self.org1.slug})
        # URL to all units from organization 2
        url2 = reverse_lazy("orgunit-list", kwargs={'org_slug': self.org2.slug})

        response1 = self.client.post(
            url1, {"rem-manager": self.egon.uuid, "orgunit": self.unit1.pk})
        response2 = self.client.post(
            url2, {"rem-manager": self.kjeld.uuid, "orgunit": self.unit3.pk})

        self.assertEqual(response1.status_code, 404)
        self.assertEqual(response2.status_code, 404)
        self.assertTrue(
            Position.objects.filter(
                account=self.egon,
                unit=self.unit1,
                role="manager").exists())
        self.assertTrue(
            Position.objects.filter(
                account=self.kjeld,
                unit=self.unit3,
                role="manager").exists())
