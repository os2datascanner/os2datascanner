"""Remove the document reports associated with the given account and
scanner job, if the job is not currently running."""

from django.core.management.base import BaseCommand

from ....organizations.models import Account
from ...models.scannerjobs.scanner import Scanner
from ...signals import publish_events

from os2datascanner.engine2.pipeline.messages import CleanMessage


class Command(BaseCommand):

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "account",
            help="the username of the account to clean up")
        parser.add_argument(
            "scanner",
            help="the primary key of the scanner to clean up")

    def handle(self, account, scanner, *args, **options):
        account_obj = Account.objects.filter(username=account).first()
        scanner_obj = Scanner.objects.filter(pk=scanner).first()
        if not account_obj:
            print(f"Account with username “{account}” does not exist.")
        if not scanner_obj:
            print(f"Scanner with primary key “{scanner}” does not exist.")
        elif scanner_obj.statuses.last() and not scanner_obj.statuses.last().finished:
            print(f"Scanner “{scanner_obj.name}” is currently running. Doing nothing.")
        elif scanner_obj and account_obj:
            message = CleanMessage(account_uuid=str(account_obj.uuid), scanner_pk=scanner_obj.pk)
            publish_events([message])
