from django.test import TestCase, RequestFactory, override_settings
from django.urls.base import reverse
from django.contrib.auth.models import AnonymousUser

from os2datascanner.projects.report.organizations.models import (
    Alias, AliasType, Account, Organization, OrganizationalUnit)
from os2datascanner.core_organizational_structure.models.position import Role
from ..organizations.models import Position
from ..reportapp.views.user_views import AccountView


class TestAccountView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        org = Organization.objects.create(name='test_org')
        self.ou = OrganizationalUnit.objects.create(name='test_ou', organization=org)
        self.account = Account.objects.create(username='name', organization=org)
        self.user = self.account.user
        self.other_account = Account.objects.create(username='someone else', organization=org)

    def test_user_page_as_roleless_user(self):
        """A user without a role should be able to see the page."""
        view = self.get_userpage_object()
        self.assertEqual(view.status_code, 200, "Roleless user did not correctly enter user page")

    def test_user_page_as_roleless_superuser(self):
        """A superuser without a role should be able to see the page."""
        self.user.is_superuser = True
        self.user.save()
        view = self.get_userpage_object()
        self.assertEqual(
            view.status_code,
            200,
            "Roleless superuser did not correctly enter user page")

    @override_settings(LANGUAGE_CODE='en-US', LANGUAGES=(('en', 'English'),))
    def test_user_page_as_dpo_user(self):
        Position.objects.create(account=self.user.account, unit=self.ou, role=Role.DPO)

        """A DPO should be able to see the page, and the DPO-role should be
        displayed."""
        view = self.get_userpage_object()
        self.assertEqual(view.status_code, 200, "DPO user did not correctly enter user page")
        # This test needs a new assertion, when we know what we want to present
        # to the user.
        # self.assertInHTML('<li>DPO</li>', view.rendered_content, 1,
        #                   "The DPO role is not displayed to the user")

    def test_anonymous_user_redirect(self):
        """A user who is not logged in should be redirected."""
        request = self.factory.get('/account')
        request.user = AnonymousUser()
        response = AccountView.as_view()(request)
        self.assertEqual(
            response.status_code,
            302,
            "Anonymous user was not correctly redirected to the login page")

    def test_user_aliases_are_sent_to_user_view_context(self):
        """The aliases connected to an account should be displayed on that
        account's page."""
        Alias.objects.create(
            user=self.user,
            account=self.account,
            _value='name@service.com',
            _alias_type=AliasType.EMAIL
        )
        Alias.objects.create(
            user=self.user,
            account=self.account,
            _value='name_alias',
            _alias_type=AliasType.GENERIC
        )

        view = self.get_userpage_object()
        self.assertIn('name@service.com',
                      str(view.context_data['aliases']),
                      "Email alias of user is not correctly sent to user view context")
        self.assertIn('name_alias',
                      str(view.context_data['aliases']),
                      "Generic alias of user is not correctly sent to user view context")

    @override_settings(LANGUAGE_CODE='en-US', LANGUAGES=(('en', 'English'),))
    def test_superuser_can_see_is_superuser_checkmark(self):
        """A superuser should be able to see their superuser checkmark."""
        self.user.is_superuser = True
        self.user.save()
        view = self.get_userpage_object()
        self.assertInHTML('<td>Superuser</td>', view.rendered_content, 1,
                          "The is_superuser attribute checkmark is not displayed to a superuser")

    @override_settings(LANGUAGE_CODE='en-US', LANGUAGES=(('en', 'English'),))
    def test_non_superuser_can_not_see_is_superuser_checkmark(self):
        """A user, who is not a superuser, should not see a superuser
        checkmark."""
        view = self.get_userpage_object()
        self.assertInHTML('<td>Superuser</td>', view.rendered_content, 0,
                          "The is_superuser attribute checkmark is displayed to a non-superuser")

    @override_settings(LANGUAGE_CODE='en-US', LANGUAGES=(('en', 'English'),))
    def test_user_can_see_link_to_password_change(self):
        """Users should be able to see a link to password change."""
        view = self.get_userpage_object()
        url = '<a class="password-change" href="%s">Change</a>' % reverse('password_change')
        self.assertInHTML(
            url,
            view.rendered_content,
            1,
            "The 'change password'-link is not displayed to the user")

    def test_access_other_user_account(self):
        """A user should not be able to access the page of another account."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('account', kwargs={'pk': self.other_account.pk}))

        self.assertEqual(response.status_code, 404,
                         "User was allowed to see other user's account.")

    def test_access_other_user_account_as_superuser(self):
        """A superuser should be able to access the page of another account."""
        self.user.is_superuser = True
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.get(reverse('account', kwargs={'pk': self.other_account.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['account'], self.other_account,
                         "The wrong account was shown!")

    def get_userpage_object(self):
        request = self.factory.get('/account')
        request.user = self.user
        response = AccountView.as_view()(request)
        return response
