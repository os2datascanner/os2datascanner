from django.test import TestCase, RequestFactory
from django.utils.text import slugify
from django.contrib.auth import get_user_model

from ..adminapp.views.exchangescanner_views import ExchangeScannerCreate
from ..core.models import Administrator
from ..core.models.client import Client
from ..organizations.models import OrganizationalUnit
from ..organizations.models.organization import Organization


class ExchangeScannerViewsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        client1 = Client.objects.create(name="client1")

        magenta_org = Organization.objects.create(
            name="Magenta ApS",
            uuid="5d02dfd3-b31c-4076-b2d5-4e41d3442952",
            slug=slugify("Magenta ApS"),
            client=client1,
        )

        magenta_org_unit0 = OrganizationalUnit.objects.create(
            name="Magenta Org. Unit",
            uuid="c0f966ea-af0f-4e81-bd65-b0967a47c3a7",
            organization=magenta_org,
        )

        magenta_org_unit1 = OrganizationalUnit.objects.create(
            name="Magenta Org. Unit1",
            uuid="20e842fc-2671-4e85-8217-454cb01b18ec",
            parent=magenta_org_unit0,
            organization=magenta_org,
        )

        OrganizationalUnit.objects.create(
            name="Magenta Org. Unit2",
            uuid="b50e34c2-4e61-4cae-b08d-19fac55d3e35",
            parent=magenta_org_unit1,
            organization=magenta_org,
        )

        client2 = Client.objects.create(name="client2")
        test_org = Organization.objects.create(
            name="Test",
            uuid="bddb5188-1240-4733-8700-b57ba6228850",
            slug=slugify("Test"),
            client=client2,
        )

        test_org_unit0 = OrganizationalUnit.objects.create(
            name="Test Org. Unit",
            uuid="466c3f4e-3f64-4c9b-b6ae-26726721a28f",
            organization=test_org,
        )

        OrganizationalUnit.objects.create(
            name="Test Org. Unit1",
            uuid="d063b582-fcd5-4a36-a99a-7785321de083",
            parent=test_org_unit0,
            organization=test_org,
        )

        OrganizationalUnit.objects.create(
            name="Test Org. Unit2",
            uuid="4cae2e75-fd10-428e-aa53-6f077da53d51",
            organization=test_org,
        )

    def setUp(self):
        self.factory = RequestFactory()
        self.kjeld = get_user_model().objects.create_user(
            username='kjeld', email='kjeld@jensen.com', password='top_secret')

    def test_exchangesscanner_org_units_list_as_administrator(self):
        """Note that this is not a django administrator role,
        but instead an organization administrator."""
        Administrator.objects.create(
            user=self.kjeld,
            client=Client.objects.get(name="client1"),
        )
        context = self.get_exchangescanner_context()
        tree_queryset = context['org_units']
        self.assertEqual(len(tree_queryset), 3)
        self.assertEqual(str(tree_queryset[0].uuid),
                         "c0f966ea-af0f-4e81-bd65-b0967a47c3a7")
        self.assertEqual(str(tree_queryset[1].uuid),
                         "20e842fc-2671-4e85-8217-454cb01b18ec")
        self.assertEqual(str(tree_queryset[2].uuid),
                         "b50e34c2-4e61-4cae-b08d-19fac55d3e35")
        self.assertEqual(str(tree_queryset[2].parent.uuid),
                         str(tree_queryset[1].uuid))

    def test_exchangescanner_org_units_list_as_superuser(self):
        self.kjeld.is_superuser = True
        context = self.get_exchangescanner_context()
        tree_queryset = context['org_units']
        self.assertEqual(len(tree_queryset), 6)
        self.assertEqual(str(tree_queryset[3].uuid),
                         "466c3f4e-3f64-4c9b-b6ae-26726721a28f")
        self.assertEqual(str(tree_queryset[4].parent.uuid),
                         str(tree_queryset[3].uuid))
        self.kjeld.is_superuser = False

    def test_exchangescanner_org_units_list_as_normal_user(self):
        context = self.get_exchangescanner_context()
        tree_queryset = context['org_units']
        self.assertEqual(len(tree_queryset), 0)

    def get_exchangescanner_context(self):
        request = self.factory.get('/exchangescanners/add/')
        request.user = self.kjeld
        response = ExchangeScannerCreate.as_view()(request)
        return response.context_data