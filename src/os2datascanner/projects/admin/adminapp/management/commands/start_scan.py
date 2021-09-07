from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

from os2datascanner.projects.admin.adminapp.models.scannerjobs.\
    scanner_model import Scanner


class Command(BaseCommand):
    """Schedule a scanner job for execution by the pipeline, just as the user
    interface's "Run" button does."""
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "id",
            type=int,
            help="the primary key of the scanner job to start",
            default=None)

    def handle(self, id, *args, **options):
        try:
            scanner = Scanner.objects.select_subclasses().get(pk=id)
        except ObjectDoesNotExist:
            print(f"no scanner job exists with id {id}")
            exit(1)

        print(scanner.run())
