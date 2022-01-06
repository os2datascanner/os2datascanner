from django.db import migrations
from ..utils import get_presentation


def bulk_update_document_report_sort_key(apps, schema_editor):
    DocumentReport = apps.get_model("os2datascanner_report", "DocumentReport")
    chunk = []

    # Using iterator() to save memory.
    # Its default chunk size is 2000, here we specify it to be explicit
    # and make it clear why we use modulus 2000.
    for i, doc_rep in enumerate(
            DocumentReport.objects.all().iterator(chunk_size=2000)):
        try:
            handle = get_presentation(doc_rep)
            if not handle:
                continue

            # ensure we don't try to put more chars into the db-fields than there's room for.
            # failing to do this will result in a django.db.DataError exception
            doc_rep.sort_key = handle.sort_key[:256]
        except Exception as e:
            print(
                f"Exception {type(e).__name__}\t"
                f"report={doc_rep.pk}\t"
                f"e={e}"
            )
            continue

        chunk.append(doc_rep)

        if i % 2000 == 0 and chunk:
            DocumentReport.objects.bulk_update(chunk, ["sort_key"])
            chunk.clear()

    if chunk:
        DocumentReport.objects.bulk_update(chunk, ["sort_key"])


class Migration(migrations.Migration):

    dependencies = [
        ('os2datascanner_report', '0038_documentreport_scanner_job_name'),
    ]

    operations = [
        migrations.RunPython(bulk_update_document_report_sort_key,
                             reverse_code=migrations.RunPython.noop)
    ]
