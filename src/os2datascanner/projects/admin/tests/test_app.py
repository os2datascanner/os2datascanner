# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2datascanner is developed by Magenta in collaboration with the OS2 public
# sector open source network <https://os2.eu/>.
#
"""
Unit tests for OS2datascanner.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.text import slugify

from os2datascanner.projects.admin.core.models.administrator import Administrator
from os2datascanner.projects.admin.organizations.models.organization import Organization
from os2datascanner.projects.admin.core.models.client import Client
from os2datascanner.projects.admin.adminapp.models.authentication import Authentication
from os2datascanner.projects.admin.adminapp.models.scannerjobs.scanner import Scanner
from os2datascanner.projects.admin.adminapp.models.scannerjobs.webscanner import WebScanner
from os2datascanner.projects.admin.adminapp.models.scannerjobs.filescanner import FileScanner
from os2datascanner.projects.admin.adminapp.validate import validate_domain


class ScannerTest(TestCase):

    """Test running a scan and domain validation."""
    # TODO: Capture the interaction so these tests can work without an
    # Internet connection! !!!

    def setUp(self):
        client1 = Client.objects.create(name="client1")
        self.magenta = Organization.objects.create(
            name="Magenta",
            uuid="b560361d-2b1f-4174-bb03-55e8b693ad0c",
            slug=slugify("Magenta"),
            client=client1,)

        client2 = Client.objects.create(name="client2")
        self.example = Organization.objects.create(
            name="IANA (example.com)",
            slug=slugify("IANA (example.com)"),
            uuid="a3575dec-8d92-4266-a8d1-97b7b84817c0",
            client=client2,)

        self.test_user = User.objects.create_user(
            username="testuser",
            password="hemmeligt",)

        Administrator.objects.create(
            user=self.test_user,
            client=client1,)

        self.invalid_webscanner = WebScanner.objects.create(
            url="http://www.example.com/",
            name="invalid webscanner",
            validation_status=Scanner.INVALID,
            organization=self.magenta)

    def test_unvalidated_scannerjob_cannot_be_started(self):
        """This test method is sufficient for all types of scanners."""

        self.client.login(username="testuser", password="hemmeligt")
        response = self.client.get("/webscanners/" + str(self.invalid_webscanner.pk) + "/askrun/")
        self.assertEqual(response.context["ok"], False)
        self.assertEqual(response.context["error_message"], Scanner.NOT_VALIDATED)

    def test_validate_domain(self):
        """Test validating domains."""
        # Make sure example.com does not validate in any of the possible
        # methods
        all_methods = [WebScanner.WEBSCANFILE, WebScanner.METAFIELD]

        for validation_method in all_methods:
            webscanner = WebScanner(
                url="http://www.example.com/",
                validation_method=validation_method,
                organization=self.example,
                pk=2
            )
            webscanner.save()
            self.assertFalse(validate_domain(webscanner))

    def test_engine2_filescanner(self):
        authentication = Authentication(username="jens")
        authentication.set_password("rigtig heste batteri haefteklamme")
        scanner = FileScanner(
                url="//ORG/SIKKERSRV",
                organization=self.magenta,
                authentication=authentication,
                alias="K")

        source_generator = scanner.generate_sources()
        engine2_source = next(source_generator)

        self.assertEqual(engine2_source.driveletter, "K")
