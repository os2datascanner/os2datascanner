"""Explore the Sources that a given scanner job represents."""

from django.core.management.base import BaseCommand

from os2datascanner.engine2.demo import url_explorer
from os2datascanner.engine2.model.core import SourceManager
from os2datascanner.projects.admin.adminapp.models.scannerjobs.scanner_model \
        import Scanner


def model_pk(model, constructor=int):
    def _pk(s):
        return model.objects.select_subclasses().get(pk=constructor(s))
    return _pk


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
                "scanners",
                help="a scanner job primary key to summarise",
                type=model_pk(Scanner),
                metavar="PK",
                nargs="+")
        url_explorer.add_control_arguments(parser)

    def handle(
            self, scanners, *,
            guess, summarise, metadata, max_depth, **kwargs):
        with SourceManager() as sm:
            for scanner in scanners:
                for source in scanner.generate_sources():
                    url_explorer.print_source(
                            sm, source,
                            guess=guess,
                            summarise=summarise,
                            metadata=metadata,
                            max_depth=max_depth)
