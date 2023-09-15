from django.test import TestCase
from django.urls import reverse_lazy

from ..organizations.models import Account, Organization


class TestSupportButtonView(TestCase):

    def setUp(self):
        self.org = Organization.objects.create(name='PPTH')
        self.account = Account.objects.create(
            username='house',
            organization=self.org,
            first_name='Gregory',
            last_name='House')
        self.user = self.account.user
        self.client.force_login(self.user)
        self.url = reverse_lazy('support_button')

    def test_support_button_view_configuration_true(self):
        """Users should be able to access the SupportButtonView, as long as
        their organization has toggled the functionality on."""

        self.org.show_support_button = True
        self.org.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_support_button_view_configuration_false(self):
        """If the user's organization has toggled the functionality off, the
        user should be denied access."""

        self.org.show_support_button = False
        self.org.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)
