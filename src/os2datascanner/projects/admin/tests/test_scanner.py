import django
from django.utils.text import slugify

from os2datascanner.projects.admin.core.models.client import Client
from os2datascanner.projects.admin.organizations.models.organization import Organization
from os2datascanner.projects.admin.adminapp.models.rules.regexrule_model import RegexRule, RegexPattern
from os2datascanner.projects.admin.adminapp.models.sensitivity_level import Sensitivity
from os2datascanner.projects.admin.adminapp.models.scannerjobs.webscanner_model import WebScanner


class ScannerTest(django.test.TestCase):
    def test_run_scan(self):
        """
        Test running a scan.
        """

        # create organisations
        client1 = Client.objects.create(name="client1")
        self.magenta_org = Organization.objects.create(
            name="Magenta",
            uuid="b560361d-2b1f-4174-bb03-55e8b693ad0c",
            slug=slugify("Magenta"),
            client=client1, )
        client2 = Client.objects.create(name="client2")
        self.theydontwantyouto_org = Organization.objects.create(
            name="IANA (example.com)",
            slug=slugify("IANA (example.com)"),
            uuid="a3575dec-8d92-4266-a8d1-97b7b84817c0",
            client=client2,)
        # create scanners
        self.magenta_scanner = WebScanner(
            name="Magenta",
            url="http://magenta.dk",
            organization=self.magenta_org,
            validation_status=WebScanner.VALID,
            download_sitemap=False,
        )
        self.theydontwantyouto_scanner = WebScanner(
            name="TheyDontWantYouTo",
            url="http://theydontwantyou.to",
            organization=self.theydontwantyouto_org,
            validation_status=WebScanner.VALID,
            download_sitemap=False,
        )
        self.magenta_scanner.save()
        self.theydontwantyouto_scanner.save()
        # create Rules and rulesets
        self.reg1 = RegexPattern(pattern_string='fællesskaber', pk=1)
        self.reg2 = RegexPattern(pattern_string='Ombudsmand', pk=2)
        self.reg3 = RegexPattern(pattern_string='projektnetwerk', pk=3)
        self.reg4 = RegexPattern(pattern_string='secure', pk=4)
        self.reg5 = RegexPattern(pattern_string='control', pk=5)
        self.reg6 = RegexPattern(pattern_string='breathe', pk=6)
        self.reg1.save()
        self.reg2.save()
        self.reg3.save()
        self.reg4.save()
        self.reg5.save()
        self.reg6.save()

        # Create rule sets
        self.tr_set1 = RegexRule(name='MagentaTestRule1', sensitivity=Sensitivity.OK, organization=self.magenta_org,
                                 pk=1)
        self.tr_set2 = RegexRule(name='TheyDontWantYouToKnow', sensitivity=Sensitivity.OK,
                                 organization=self.theydontwantyouto_org, pk=2)
        self.tr_set1.save()
        self.tr_set2.save()
        self.tr_set1.patterns.add(self.reg1)
        self.tr_set1.patterns.add(self.reg2)
        self.tr_set1.patterns.add(self.reg3)
        self.tr_set2.patterns.add(self.reg4)
        self.tr_set1.save()
        self.tr_set2.save()

        self.magenta_scanner.rules.add(self.tr_set1)
        self.magenta_scanner.save()

        self.magenta_scanner.run()

        # TODO: Now what?
