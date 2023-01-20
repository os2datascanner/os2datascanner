from django.test import TestCase
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from ..models import Organization
from ...core.models import Client, Administrator


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

        self.assertContains(response, "client_list")
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

        self.assertContains(response, "client_list")
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
        expected_code = 404

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
        expected_code = 404

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
