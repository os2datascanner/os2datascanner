from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.core.management.base import CommandError

from ..adminapp.models.scannerjobs.scanner import Scanner, ScanStatus
from ..organizations.models import Account, Organization


class CleanAccountResultsTests(TestCase):

    def call_command(self, *args, **kwargs):
        err = StringIO()
        call_command(
            "cleanup_account_results",
            *args,
            stdout=StringIO(),
            stderr=err,
            **kwargs
        )

        return err.getvalue()

    def test_invalid_account(self):
        """Calling the command with an invalid username should raise a
        CommandError."""

        scanner = Scanner.objects.create(name="SomeScanner")

        self.assertRaises(
            CommandError,
            lambda: self.call_command(
                accounts=["invalidAccount"],
                scanners=[
                    scanner.pk]))

    def test_invalid_scanner(self):
        """Calling the command with an invalid scanner pk should raise a
        CommandError."""

        account = Account.objects.create(
            username="Bøffen",
            organization=Organization.objects.first())

        self.assertRaises(
            CommandError,
            lambda: self.call_command(
                accounts=[
                    account.username],
                scanners=[100]))

    def test_running_scanner(self):
        """Calling the command specifying a running scanner should write
        something to stderr."""
        account = Account.objects.create(
            username="Bøffen",
            organization=Organization.objects.first())
        scanner = Scanner.objects.create(
            name="SomeScanner",
            organization=Organization.objects.first())
        ScanStatus.objects.create(scanner=scanner,
                                  scan_tag=scanner._construct_scan_tag().to_json_object())

        self.assertRaises(CommandError, lambda: self.call_command(
                accounts=[
                    account.username], scanners=[
                    scanner.pk]))
