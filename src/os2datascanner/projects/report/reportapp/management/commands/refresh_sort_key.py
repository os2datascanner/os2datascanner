from django.core.management.base import BaseCommand

from ...models.documentreport import DocumentReport
from ...utils import get_presentation, prepare_json_object


class Command(BaseCommand):
    """Update every DocumentReport's cache fields with values produced by the
    current implementation of the Handle.sort_key and Handle.presentation_name
    functions."""

    help = __doc__

    def handle(self, *args, **options):
        queryset = DocumentReport.objects.all()
        for report in queryset.iterator():
            try:
                handle = get_presentation(report)
                if not handle:
                    continue
                # ensure we don't try to put more chars into the db-fields than there's room for.
                # failing to do this will result in a django.db.DataError exception
                report.sort_key = handle.sort_key[:256]
                report.name = prepare_json_object(handle.presentation_name)
                report.save()

            except Exception as e:
                print(
                    f"Exception {type(e).__name__}\t"
                    f"report={report}\t"
                    f"e={e}"
                )
                raise
        self.stdout.write(self.style.SUCCESS("Refreshed sort keys!"))
