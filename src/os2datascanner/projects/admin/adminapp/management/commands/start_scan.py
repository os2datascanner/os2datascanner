import sys
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext, gettext_lazy as _

from os2datascanner.projects.admin.adminapp.models.scannerjobs.scanner import (
        Scanner)


class Command(BaseCommand):
    """Schedule a scanner job for execution by the pipeline, just as the user
    interface's "Run" button does."""
    help = ugettext(__doc__)

    def add_arguments(self, parser):
        parser.add_argument(
            "id",
            type=int,
            help=_("the primary key of the scanner job to start"),
            default=None)
        parser.add_argument(
            "--checkups-only",
            help=_("only scan objects previously scheduled for a checkup"),
            action="store_true")

    def handle(self, id, *args, checkups_only, **options):
        try:
            scanner = Scanner.objects.select_subclasses().get(pk=id)
        except ObjectDoesNotExist:
            print(_("no scanner job exists with id {id}").format(id=id))
            sys.exit(1)

        print(scanner.run(explore=not checkups_only))
