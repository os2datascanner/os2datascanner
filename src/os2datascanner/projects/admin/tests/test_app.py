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
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )
"""Unit tests for OS2Webscanner.

These will pass when you run "manage.py test os2webscanner".
"""

from django.test import TestCase
from django.contrib.auth.models import User

from os2datascanner.projects.admin.adminapp.models.organization_model import Organization
from os2datascanner.projects.admin.adminapp.models.userprofile_model import UserProfile
from os2datascanner.projects.admin.adminapp.models.authentication_model import Authentication
from os2datascanner.projects.admin.adminapp.models.scannerjobs.scanner_model import Scanner
from os2datascanner.projects.admin.adminapp.models.scannerjobs.webscanner_model import WebScanner
from os2datascanner.projects.admin.adminapp.models.scannerjobs.filescanner_model import FileScanner
from os2datascanner.projects.admin.adminapp.validate import validate_domain


class ScannerTest(TestCase):

    """Test running a scan and domain validation."""
    # TODO: Capture the interaction so these tests can work without an
    # Internet connection! !!!

    def setUp(self):
        """Setup some data to test with."""
        # Don't change the order of these, because Magenta needs
        # pk = 2 to pass the validation test

        self.magenta = Organization(name="Magenta", pk=1)
        self.magenta.save()
        self.example = Organization(name="IANA (example.com)", pk=2)
        self.example.save()

        self.test_user = User.objects.create_user(username='testuser',
                                                  password='hemmeligt')

        self.user_profile = UserProfile.objects.create(user=self.test_user,
                                                       organization=self.magenta)

        self.invalid_webscanner = WebScanner.objects.create(
            url="http://www.example.com/",
            name='invalid webscanner',
            validation_status=Scanner.INVALID,
            organization=self.magenta)

    def test_unvalidated_scannerjob_cannot_be_started(self):
        """This test method is sufficient for all types of scanners."""

        self.client.login(username='testuser', password='hemmeligt')
        response = self.client.get('/webscanners/' + str(self.invalid_webscanner.pk) + '/askrun/')
        self.assertEqual(response.context['ok'], False)
        self.assertEqual(response.context['error_message'], Scanner.NOT_VALIDATED)

    def test_validate_domain(self):
        """Test validating domains."""
        # Make sure example.com does not validate in any of the possible
        # methods
        all_methods = [WebScanner.WEBSCANFILE, WebScanner.METAFIELD]

        for validation_method in all_methods:
            domain = WebScanner(url="http://www.example.com/",
                            validation_method=validation_method,
                            organization=self.example,
                            pk=2)
            domain.save()
            self.assertFalse(validate_domain(domain))

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

