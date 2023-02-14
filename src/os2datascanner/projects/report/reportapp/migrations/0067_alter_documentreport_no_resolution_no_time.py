from django.db import migrations

def check_resolution_remove_resolution_time(apps, schema_editor):
    """Set the resolution time of reports with no resolution status to None"""

    DocumentReport = apps.get_model("os2datascanner_report", "DocumentReport")

    DocumentReport.objects.filter(resolution_status__isnull=True, resolution_time__isnull=False).update(resolution_time=None)


class Migration(migrations.Migration):

    dependencies = [
        ('os2datascanner_report', '0066_documentreport_owner'),
    ]

    operations = [
        migrations.RunPython(check_resolution_remove_resolution_time, reverse_code=migrations.RunPython.noop),
    ]