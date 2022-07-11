import sys
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

from os2datascanner.projects.admin.adminapp.models.scannerjobs.\
    scanner_model import Scanner


class Command(BaseCommand):
    """Command for starting a pipeline collector process."""
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "id",
            type=int,
            help="The id of the exchange scannerjob.",
            default=None)

    def handle(self, id, *args, **options):
        try:
            scanner = Scanner.objects.select_subclasses().get(pk=id)
        except ObjectDoesNotExist:
            print(f"no exchange scannerjob exists with id {id}")
            sys.exit(1)

        print(scanner.verify())
