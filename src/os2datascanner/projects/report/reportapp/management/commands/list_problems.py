from django.core.management.base import BaseCommand
from os2datascanner.projects.report.reportapp.models.documentreport_model import DocumentReport


class Command(BaseCommand):
    """List the problems for a scanner job."""

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "pk",
            type=int,
            help="Primary key of scanner job",
            default=None,
        )
        parser.add_argument(
            "--head",
            type=int,
            help="Only show *HEAD* first problems",
        )

    def handle(self, pk, *args, **options):
        docs = DocumentReport.objects.filter(
            raw_scan_tag__scanner__pk=pk
        ).filter(raw_problem__isnull=False)

        head = options.get("head")
        if head is not None:
            docs = docs[:head]

        for doc in docs:
            msg = doc.problem.message
            uri = doc.problem.handle.presentation
            self.stdout.write(f"{msg}: {uri}")
