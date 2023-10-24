from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from ..organizations.models import Account, Organization
from ..reportapp.views.report_views import UserReportView


class TestLoginRequired(TestCase):

    def setUp(self):
        org = Organization.objects.create(name="Team Saftevand")
        self.account = Account.objects.create(
            username='Yvonne', first_name="Yvonne",
            last_name="Solbærsaft", organization=org)
        self.factory = RequestFactory()

    def test_index_anonymous_user(self):
        # Tries to hit path "/" with no login
        request = self.factory.get('/')
        request.user = AnonymousUser()
        response = UserReportView.as_view()(request)
        self.assertEqual(response.status_code, 302)

    def test_index_as_user(self):
        # Tries to hit path "/" as user
        request = self.factory.get('/')
        user = self.account.user
        request.user = user
        response = UserReportView.as_view()(request)

        # Should get status code 200 OK and index.html template
        self.assertEqual(response.status_code, 200)
        self.assertIn("index.html", response.template_name)
        self.account.delete()
