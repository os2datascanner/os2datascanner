from django.core.management.base import BaseCommand

from ...models.documentreport_model import DocumentReport
from ...utils import get_presentation


class Command(BaseCommand):
    """ When run, updates every DocumentReport's sort_key value
    with it's handles current implementation of sort_key."""

    help = __doc__

    def handle(self, *args, **options):
        queryset = DocumentReport.objects.all()
        for report in queryset.iterator():
            try:
                handle = get_presentation(report)
                if not handle:
                    continue
                # ensure we don't try to put more chars into the db-fields than there's room for.
                # failing to do this will result in an django.db.DataError exception
                sort_key = handle.sort_key[:256]
                report.sort_key = sort_key
                report.save()

            except Exception as e:
                print(
                    f"Exception {type(e).__name__}\t"
                    f"report={report}\t"
                    f"e={e}"
                )
                raise
        self.stdout.write(self.style.SUCCESS("Refreshed sort keys!"))
