from datetime import datetime
from dateutil.tz import gettz
from parameterized import parameterized

from django.contrib.auth.models import User, AnonymousUser
from django.test import RequestFactory, TestCase
from django.utils.text import slugify

from ..adminapp.views.webscanner_views import WebScannerList
from ..adminapp.models.scannerjobs.webscanner_model import WebScanner
from ..adminapp.models.rules.rule_model import Rule
from ..adminapp.views.rule_views import RuleList
from ..adminapp.views.scanner_views import StatusOverview
from ..adminapp.models.scannerjobs.scanner_model import Scanner, ScanStatus
from ..core.models import Client, Administrator
from ..organizations.models import Organization
from ..organizations.views import OrganizationListView


class ListViewsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        client1 = Client.objects.create(name="client1")
        Organization.objects.create(
            name="Magenta",
            uuid="b560361d-2b1f-4174-bb03-55e8b693ad0c",
            slug=slugify("Magenta"),
            client=client1,
        )
        client2 = Client.objects.create(name="client2")
        Organization.objects.create(
            name="IANA (example.com)",
            slug=slugify("IANA (example.com)"),
            uuid="a3575dec-8d92-4266-a8d1-97b7b84817c0",
            client=client2,
        )
        WebScanner.objects.create(
            name="Magenta",
            url="http://magenta.dk",
            organization=Organization.objects.get(
                uuid="b560361d-2b1f-4174-bb03-55e8b693ad0c"),
            validation_status=WebScanner.VALID,
            download_sitemap=False,
        )
        WebScanner.objects.create(
            name="TheyDontWantYouTo",
            url="http://theydontwantyou.to",
            organization=Organization.objects.get(
                uuid="a3575dec-8d92-4266-a8d1-97b7b84817c0"),
            validation_status=WebScanner.VALID,
            download_sitemap=False,
        )
        Rule.objects.create(name="Ny regel",
                            organization=Organization.objects.get(
                                uuid="b560361d-2b1f-4174-bb03-55e8b693ad0c"),
                            description="Helt ny regel",
                            )
        Rule.objects.create(name="Ny regel 2",
                            organization=Organization.objects.get(
                                uuid="a3575dec-8d92-4266-a8d1-97b7b84817c0"),
                            description="Helt ny regel 2",
                            )
        ScanStatus.objects.create(
            scan_tag={"time": datetime.now(tz=gettz()).isoformat()},
            scanner=Scanner.objects.get(name="Magenta")
        )
        ScanStatus.objects.create(
            scan_tag={"time": datetime.now(tz=gettz()).isoformat()},
            scanner=Scanner.objects.get(name="TheyDontWantYouTo")
        )

    def setUp(self) -> None:
        super().setUp()
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='kjeld', email='kjeld@jensen.com', password='top_secret')

    def get_path_and_class():
        params = [
            ("WebscannerListViewTest", '/webscanners/', WebScannerList()),
            ("RuleListViewTest", '/rules/', RuleList()),
            ("ScanStatusListViewTest", '/status/', StatusOverview()),
            ("OrganizationListViewTest", '/organizations/', OrganizationListView()),
        ]
        return params

    def test_view_as_anonymous_user(self):
        request = self.factory.get('/webscanners')
        request.user = AnonymousUser()
        response = WebScannerList.as_view()(request)
        self.assertNotEqual(response.status_code, 200)

    @parameterized.expand(get_path_and_class)
    def test_as_superuser(self, _, path, list_type):
        self.user.is_superuser = True
        qs = self.listview_get_queryset(path, list_type)
        if isinstance(list_type, RuleList):
            self.assertEqual(len(qs), 3)
        elif isinstance(list_type, OrganizationListView):
            # Migrations 0042 adds os2datascanner as an organization
            # and that is why we expect 3 organizations listed as superuser.
            self.assertEqual(len(qs), 3)
        else:
            self.assertEqual(len(qs), 2)

    @parameterized.expand(get_path_and_class)
    def test_as_user(self, _, path, list_type):
        qs = self.listview_get_queryset(path, list_type)
        self.assertEqual(len(qs), 0)

    @parameterized.expand(get_path_and_class)
    def test_as_administrator_for_magenta_org(self, _, path, list_type):
        administrator = Administrator.objects.create(
            user=self.user,
            client=Client.objects.get(name="client1")
        )
        qs = self.listview_get_queryset(path, list_type)
        self.assertEqual(len(qs), 1)
        if isinstance(list_type, StatusOverview):
            self.assertEqual(qs.first().scanner.organization.name, "Magenta")
        elif isinstance(list_type, OrganizationListView):
            self.assertEqual(qs.first().organizations.first().name,
                             "Magenta")
        else:
            self.assertEqual(qs.first().organization.name, "Magenta")
        administrator.delete()

    @parameterized.expand(get_path_and_class)
    def test_as_administrator_for_theydontwantyouto_org(self, _, path, list_type):
        administrator = Administrator.objects.create(
            user=self.user,
            client=Client.objects.get(name="client2")
        )
        qs = self.listview_get_queryset(path, list_type)
        self.assertEqual(len(qs), 1)
        if isinstance(list_type, StatusOverview):
            self.assertEqual(qs.first().scanner.organization.name,
                             "IANA (example.com)")
        elif isinstance(list_type, OrganizationListView):
            self.assertEqual(qs.first().organizations.first().name,
                             "IANA (example.com)")
        else:
            self.assertEqual(qs.first().organization.name, "IANA (example.com)")
        administrator.delete()

    def listview_get_queryset(self, path, view):
        request = self.factory.get(path)
        request.user = self.user
        view.setup(request)
        return view.get_queryset()
