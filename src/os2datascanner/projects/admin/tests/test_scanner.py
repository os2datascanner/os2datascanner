from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils.text import slugify

from os2datascanner.projects.admin.core.models.client import Client
from os2datascanner.projects.admin.organizations.models.organization \
    import Organization
from os2datascanner.projects.admin.adminapp.models.rules.regexrule_model \
    import RegexRule, RegexPattern
from os2datascanner.projects.admin.adminapp.models.sensitivity_level \
    import Sensitivity
from os2datascanner.projects.admin.adminapp.models.scannerjobs.webscanner_model \
    import WebScanner
from os2datascanner.projects.admin.adminapp.views.webscanner_views \
    import WebScannerUpdate

User = get_user_model()


class ScannerTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        # create organisations
        client1 = Client.objects.create(name="client1")
        magenta_org = Organization.objects.create(
            name="Magenta",
            uuid="b560361d-2b1f-4174-bb03-55e8b693ad0c",
            slug=slugify("Magenta"),
            client=client1, )

        client2 = Client.objects.create(name="client2")
        theydontwantyouto_org = Organization.objects.create(
            name="IANA (example.com)",
            slug=slugify("IANA (example.com)"),
            uuid="a3575dec-8d92-4266-a8d1-97b7b84817c0",
            client=client2,)

        # create scanners
        magenta_scanner = WebScanner(
            name="Magenta",
            url="http://magenta.dk",
            organization=magenta_org,
            validation_status=WebScanner.VALID,
            download_sitemap=False,
        )
        theydontwantyouto_scanner = WebScanner(
            name="TheyDontWantYouTo",
            url="http://theydontwantyou.to",
            organization=theydontwantyouto_org,
            download_sitemap=False,
        )
        magenta_scanner.save()
        theydontwantyouto_scanner.save()

        # create Rules and rulesets
        reg1 = RegexPattern(pattern_string='fællesskaber', pk=1)
        reg2 = RegexPattern(pattern_string='Ombudsmand', pk=2)
        reg3 = RegexPattern(pattern_string='projektnetwerk', pk=3)
        reg4 = RegexPattern(pattern_string='secure', pk=4)
        reg5 = RegexPattern(pattern_string='control', pk=5)
        reg6 = RegexPattern(pattern_string='breathe', pk=6)
        reg1.save()
        reg2.save()
        reg3.save()
        reg4.save()
        reg5.save()
        reg6.save()

        # Create rule sets
        tr_set1 = RegexRule(
            name='MagentaTestRule1',
            sensitivity=Sensitivity.OK,
            organization=magenta_org,
            pk=1
        )
        tr_set2 = RegexRule(
            name='TheyDontWantYouToKnow',
            sensitivity=Sensitivity.OK,
            organization=theydontwantyouto_org,
            pk=2
        )
        tr_set1.save()
        tr_set2.save()
        tr_set1.patterns.add(reg1)
        tr_set1.patterns.add(reg2)
        tr_set1.patterns.add(reg3)
        tr_set2.patterns.add(reg4)
        tr_set1.save()
        tr_set2.save()

        magenta_scanner.rules.add(tr_set1)
        magenta_scanner.save()

    def setUp(self) -> None:
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='britney',
            email='britney@spears.com',
            password='top_secret'
        )

    def test_superuser_can_validate_scannerjob(self):
        self.user.is_superuser = True
        self.user.save()
        view = self.get_webscannerupdate_view()
        form_fields = view.get_form_fields()
        self.assertIn(
                      'validation_status', str(form_fields),
                      msg="No validation_status field in WebscannerUpdate get_form_fields"
                      )

    def test_user_cannot_validate_scannerjob(self):
        self.user.is_superuser = False
        self.user.save()
        view = self.get_webscannerupdate_view()
        form_fields = view.get_form_fields()
        self.assertNotIn(
            'validation_status', str(form_fields),
            msg="User not superuser but validation_status"
            "field present in WebscannerUpdate get_form_fields"
        )

    def get_webscannerupdate_view(self):
        request = self.factory.get('/')
        request.user = self.user
        view = WebScannerUpdate()
        view.setup(request)
        return view
