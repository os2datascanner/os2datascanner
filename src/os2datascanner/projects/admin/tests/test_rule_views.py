'''Tests for RuleViews in admin module.'''

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.test import Client as TestClient
from django.test.testcases import SerializeMixin
from django.utils.text import slugify

from ..adminapp.models.sensitivity_level import Sensitivity
from ..adminapp.models.rules.regexrule import RegexRule
from ..adminapp.models.rules.cprrule import CPRRule
from ..adminapp.views.rule_views import (CPRRuleCreate,
                                         CPRRuleUpdate,
                                         RegexRuleCreate)
from ..core.models import Client
from ..organizations.models import Organization


class RuleViewTestCaseMixin(SerializeMixin):
    '''Base class for all test fixtures related to rule views.'''
    lockfile = __file__

    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()

        self.user = User.objects.create_user(
            username='kjeld',
            email='kjeld@jensen.com',
            password='top_secret',
        )

        self.client = Client.objects.create(name="client1")

        self.organization = Organization.objects.create(
            name="Magenta",
            uuid="b560361d-2b1f-4174-bb03-55e8b693ad0c",
            slug=slugify("Magenta"),
            client=self.client,
        )

        self.rule = RegexRule.objects.create(
            name="En Regex Regel",
            description="En gammel regex regel.",
            organization=self.organization,
            sensitivity=Sensitivity.HIGH)

        self.test_client = TestClient()
        self.test_client.login(username='kjeld', password='top_secret')


class RegexRuleViewsTest(RuleViewTestCaseMixin, TestCase):
    '''Test fixture for rule views related to RegexRule.'''

    def test_create_regexrule(self):
        '''Check that an authenticated user can create a RegexRule.'''

        # Arrange
        fields = {
            "name": "Ny Regel",
            "description": "En helt splinterny regel.",
            "organization": self.organization.uuid,
            "sensitivity": Sensitivity.HIGH,
            "pattern_0": "test",
            "save": "",
            }

        view = RegexRuleCreate()
        request = self.factory.post('/rules/regex/add/', fields)
        request.user = self.user

        # Act
        view.setup(request)
        form = view.get_form()

        # Assert
        for prop, value in fields.items():
            self.assertEqual(form.data[prop], str(value))


class CPRRuleViewsTest(RuleViewTestCaseMixin, TestCase):
    '''Test fixture for rule views related to CPRRule.'''

    def test_create_cprrule(self):
        '''Ensure that users are allowed to create CPRRules.'''

        # Arrange
        fields = {
            "name": "Ny Regel",
            "description": "En helt splinterny regel.",
            "organization": self.organization,
            "sensitivity": Sensitivity.HIGH,
            }

        view = CPRRuleCreate()
        request = self.factory.post('/rules/cpr/add/', fields)
        request.user = self.user

        # Act
        view.setup(request)
        form = view.get_form()

        # Assert
        for prop, value in fields.items():
            self.assertEqual(form.data[prop], str(value))

    def test_update_cprrule(self):
        '''Ensure that users are allowed to update CPRRules.'''

        # Arrange
        fields = {
            "name": "Ny CPR regel",
            "organization": f"{self.organization.uuid}",
            "description": "En opdateret beskrivelse for den nye CPR regel.",
            }

        pk = CPRRule.objects.first().pk

        view = CPRRuleUpdate()
        request = self.factory.post(f'/rules/cpr/{pk}', fields)
        request.user = self.user

        # Act
        view.setup(request, pk=pk)
        form = view.get_form()

        # Assert
        for prop, value in fields.items():
            self.assertEqual(form.data[prop], str(value))
