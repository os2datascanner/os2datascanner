from django.test import TestCase
from django.urls import reverse_lazy
from django.contrib.auth.models import User

from ..models import Organization
from ...core.models import Client


class CreateOrganizationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='name', password='secret')
        self.client.force_login(self.user)
        self.mock_client = Client.objects.create(name='mock_client')

    def test_unique_name_organization(self):
        """Successfully creating an organization redirects to the list view."""
        url = reverse_lazy('add-organization-for',
                           kwargs={'client_id': self.mock_client.uuid})
        success_url = reverse_lazy('organization-list')
        response = self.client.post(url, {
            'name': 'Unique',
            'contact_email': '',
            'contact_phone': '',
        })
        self.assertRedirects(response, success_url)

    def test_same_name_organization(self):
        """Providing a name already in use for an organization
        should invalidate the form and display an error."""
        Organization.objects.create(name='Same', slug='same', client=self.mock_client)
        url = reverse_lazy('add-organization-for', kwargs={'client_id': self.mock_client.uuid})
        response = self.client.post(url, {
            'name': 'Same',
            'contact_email': '',
            'contact_phone': '',
        })
        self.assertContains(response, "That name is already taken.")
