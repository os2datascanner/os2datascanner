from django.db import models, migrations

def delete_duplicate_scanner_pk_and_path(apps, schema_editor):
    DocumentReport = apps.get_model("os2datascanner_report", "DocumentReport")

    # We want to retrieve distinct DocumentReports based on scanner PK and path field
    # to be able to filter by it, and then delete the oldest one.
    # Distinct() requires you to follow the order_by, and as we already have ordering on DocumentReports in Meta,
    # we must override it here.
    doc_reps = DocumentReport.objects.order_by(
        "data__scan_tag__scanner__pk", "path").values_list(
        "data__scan_tag__scanner__pk", "path").distinct()

    # Using iterator which has a default batch size of 2000 to protect
    # us from potentially huge datasets
    for scanner_pk, path in doc_reps.iterator():
        # Negative order_by and slicing to delete all old duplicates.
        oldest_doc_reps = DocumentReport.objects.filter(data__scan_tag__scanner__pk = scanner_pk,
                                                        path = path).order_by("-pk")[1:]

        DocumentReport.objects.filter(id__in=oldest_doc_reps).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('os2datascanner_report', '0034_documentreport_documentreport_matched'),
    ]

    operations = [
        migrations.RunPython(delete_duplicate_scanner_pk_and_path,
                             reverse_code=migrations.RunPython.noop)
    ]