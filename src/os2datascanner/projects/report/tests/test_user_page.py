from django.test import TestCase, RequestFactory, override_settings
from django.urls.base import reverse
from django.contrib.auth.models import User, AnonymousUser

from os2datascanner.projects.report.reportapp.models.roles.dpo import DataProtectionOfficer
from os2datascanner.projects.report.organizations.models import Alias, AliasType
from ..reportapp.views.user_views import UserView


class TestUserProfile(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='name', email='name@service.com', password='secret')

    def test_user_page_as_roleless_user(self):
        view = self.get_userpage_object()
        self.assertEqual(view.status_code, 200, "Roleless user did not correctly enter user page")

    def test_user_page_as_roleless_superuser(self):
        self.user.is_superuser = True
        view = self.get_userpage_object()
        self.assertEqual(
            view.status_code,
            200,
            "Roleless superuser did not correctly enter user page")

    @override_settings(LANGUAGE_CODE='en-US', LANGUAGES=(('en', 'English'),))
    def test_user_page_as_dpo_user(self):
        DataProtectionOfficer.objects.create(user=self.user)
        view = self.get_userpage_object()
        self.assertEqual(view.status_code, 200, "DPO user did not correctly enter user page")
        self.assertInHTML('<li>DPO</li>', view.rendered_content, 1,
                          "The DPO role is not displayed to the user")

    def test_anonymous_user_redirect(self):
        request = self.factory.get('/user')
        request.user = AnonymousUser()
        response = UserView.as_view()(request)
        self.assertEqual(
            response.status_code,
            302,
            "Anonymous user was not correctly redirected to the login page")

    def test_user_aliases_are_sent_to_user_view_context(self):
        aliases = []
        alias_e = Alias.objects.create(
            user=self.user,
            _value='name@service.com',
            _alias_type=AliasType.EMAIL
        )
        alias_g = Alias.objects.create(
            user=self.user,
            _value='name_alias',
            _alias_type=AliasType.GENERIC
        )
        aliases.append(alias_e)
        aliases.append(alias_g)
        self.aliases = aliases
        view = self.get_userpage_object()
        self.assertIn('name@service.com',
                      str(view.context_data['aliases']),
                      "Email alias of user is not correctly sent to user view context")
        self.assertIn('name_alias',
                      str(view.context_data['aliases']),
                      "Generic alias of user is not correctly sent to user view context")

    @override_settings(LANGUAGE_CODE='en-US', LANGUAGES=(('en', 'English'),))
    def test_superuser_can_see_is_superuser_checkmark(self):
        self.user.is_superuser = True
        view = self.get_userpage_object()
        self.assertInHTML('<td>Superuser</td>', view.rendered_content, 1,
                          "The is_superuser attribute checkmark is not displayed to a superuser")

    @override_settings(LANGUAGE_CODE='en-US', LANGUAGES=(('en', 'English'),))
    def test_non_superuser_can_not_see_is_superuser_checkmark(self):
        view = self.get_userpage_object()
        self.assertInHTML('<td>Superuser</td>', view.rendered_content, 0,
                          "The is_superuser attribute checkmark is displayed to a non-superuser")

    @override_settings(LANGUAGE_CODE='en-US', LANGUAGES=(('en', 'English'),))
    def test_user_can_see_link_to_password_change(self):
        view = self.get_userpage_object()
        url = '<a class="password-change" href="%s">Change</a>' % reverse('password_change')
        self.assertInHTML(
            url,
            view.rendered_content,
            1,
            "The 'change password'-link is not displayed to the user")

    def get_userpage_object(self):
        request = self.factory.get('/user')
        request.user = self.user
        response = UserView.as_view()(request)
        return response
