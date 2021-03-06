from django.contrib.auth.models import User, AnonymousUser
from django.test import RequestFactory, TestCase

from ..reportapp.views.views import MainPageView


class TestLoginRequired(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='Yvonne', email='yvonne@jensen.com', password='very_secret')

    def test_index_anonymous_user(self):
        # Tries to hit path "/" with no login
        request = self.factory.get('/')
        request.user = AnonymousUser()
        response = MainPageView.as_view()(request)
        self.assertEqual(response.status_code, 302)

    def test_index_as_user(self):
        # Tries to hit path "/" as user
        request = self.factory.get('/')
        user = self.user
        request.user = user
        response = MainPageView.as_view()(request)

        # Should get status code 200 OK and index.html template
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name[0], "index.html")
        user.delete()
