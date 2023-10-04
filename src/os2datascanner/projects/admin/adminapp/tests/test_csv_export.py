from django.test import TestCase
from django.conf import settings
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model

from ...organizations.models import Organization
from ..models.usererrorlog import UserErrorLog
from ..models.scannerjobs.scanner import Scanner, ScanStatus
from ...core.models import Administrator, Client


class ExportUserErrorLogTests(TestCase):
    def setUp(self):
        self.url = reverse_lazy('export-error-log')
        self.user = get_user_model().objects.create(username='mr_userman', password='hunter2')
        self.admin = get_user_model().objects.create(username='hagrid', password='shelob')
        client_obj = Client.objects.create(name='test_client')
        self.org = Organization.objects.create(name='test_org', client=client_obj)
        Administrator.objects.create(user=self.admin, client=client_obj)
        settings.USERERRORLOG = True

    def create_usererrorlogs(self, num, org=None):
        if not org:
            org = self.org
        scanner = Scanner.objects.create(
            name=f"SomeScanner-{org.name}",
            organization=org)
        status = ScanStatus.objects.create(
            scanner=scanner,
            scan_tag=scanner._construct_scan_tag().to_json_object())

        for i in range(num):
            UserErrorLog.objects.create(
                scan_status=status,
                organization=org,
                path=f"({i}) This is the way!",
                error_message="Something is wrong :(")

    def test_csv_export_usererrorlog_as_org_admin(self):
        """Admins for an organization should be able to export the usererrorlogs
        from their own organization."""
        num_errors = 11
        self.create_usererrorlogs(num_errors)

        # Creating some errors for another client, the user should not be able
        # to see these.
        other_client = Client.objects.create(name='other_client')
        other_org = Organization.objects.create(name='other_org', client=other_client)
        self.create_usererrorlogs(10, org=other_org)

        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        streamed_rows = [row for row in response.streaming_content]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(streamed_rows), num_errors+1)

    def test_csv_export_usererrorlog_unprivileged_user(self):
        """A user unrelated to an organization should only get header values."""
        num_errors = 11
        self.create_usererrorlogs(num_errors)

        self.client.force_login(self.user)
        response = self.client.get(self.url)
        streamed_rows = [row for row in response.streaming_content]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(streamed_rows), 1)

    def test_csv_export_usererrorlog_anonymous_user(self):
        """An anonymous user should be redirected."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
