"""Remove the document reports associated with the given account and
scanner job, if the job is not currently running."""

import argparse

from uuid import UUID

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

from ....organizations.models import Account
from ...models.scannerjobs.scanner import Scanner
from ...signals import publish_events
from ...utils import CleanMessage


def is_valid_uuid(string: str):
    try:
        _ = UUID(string)
        return True
    except ValueError:
        return False


class Command(BaseCommand):

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "--accounts",
            help="the usernames or UUIDs of the accounts to clean up", nargs="+", type=str)
        parser.add_argument(
            "--scanners",
            help="the primary keys of the scanners to clean up", nargs="+", type=int)
        parser.add_argument(
            "--publisher",
            help=argparse.SUPPRESS,
            type=str)

    def handle(self, *args, **options):
        account_uuids = [arg for arg in options.get("accounts", []) if is_valid_uuid(arg)]
        account_usernames = [arg for arg in options.get("accounts", []) if arg not in account_uuids]
        scanner_pks = options.get("scanners", [])

        account_objs = Account.objects.filter(
            Q(username__in=account_usernames) |
            Q(uuid__in=account_uuids))
        scanner_objs = Scanner.objects.filter(pk__in=scanner_pks)

        if account_objs.exists() and scanner_objs.exists():
            self.stdout.write("Cleaning document reports for accounts " +
                              ", ".join([account.username for account in account_objs]) +
                              " and scanners " +
                              ", ".join([scanner.name for scanner in scanner_objs]) +
                              "\n")
        else:
            if not account_objs.exists():
                raise CommandError("No accounts with the given usernames or UUIDs found.")
            if not scanner_objs.exists():
                raise CommandError("No scanners with the given primary keys found.")

        self.send_clean_message(
            account_objs,
            scanner_objs,
            publisher=options.get(
                "publisher",
                "manual"))

    def send_clean_message(self, accounts, scanners, publisher=None):
        for scanner in scanners:
            if scanner.statuses.last() and not scanner.statuses.last().finished:
                self.stderr.write(f"Scanner “{scanner.name}” is currently running.")
                scanners = scanners.exclude(pk=scanner.pk)

        if scanners.exists():
            message = CleanMessage(
                accounts=[
                    (str(
                        account.uuid),
                        account.username) for account in accounts],
                scanner_pk=[
                    scanner.pk for scanner in scanners],
                publisher=publisher,
                time=timezone.now())
            publish_events([message])
        else:
            raise CommandError("All scanners are currently running! Doing nothing.")
