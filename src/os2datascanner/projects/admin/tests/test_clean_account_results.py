from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.core.management.base import CommandError

from ..adminapp.models.scannerjobs.scanner import Scanner, ScanStatus
from ..organizations.models import Account, Organization


class CleanAccountResultsTests(TestCase):

    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "cleanup_account_results",
            *args,
            stdout=StringIO(),
            stderr=out,
            **kwargs
        )
        return out.getvalue()

    def test_invalid_account(self):
        """Calling the command with an invalid username should write a
        specific stdout."""

        scanner = Scanner.objects.create(name="SomeScanner")

        self.assertRaises(CommandError, lambda: self.call_command("invalidAccount", scanner.pk))

    def test_invalid_scanner(self):
        """Calling the command with an invalid scanner pk should write a
        specific stdout."""

        account = Account.objects.create(
            username="Bøffen",
            organization=Organization.objects.first())

        self.assertRaises(CommandError, lambda: self.call_command(account.username, 100))

    def test_running_scanner(self):
        """Calling the command specifying a running scanner should write a
        specific stdout."""
        account = Account.objects.create(
            username="Bøffen",
            organization=Organization.objects.first())
        scanner = Scanner.objects.create(
            name="SomeScanner",
            organization=Organization.objects.first())
        ScanStatus.objects.create(scanner=scanner,
                                  scan_tag=scanner._construct_scan_tag().to_json_object())

        self.assertRaises(CommandError, lambda: self.call_command(account.username, scanner.pk))
