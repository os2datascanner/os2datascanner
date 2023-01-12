from django.db import migrations, models
from django.utils import timezone


def add_start_to_calendar_reports(apps, schema_editor):
    """Access the handle in the raw_metadata and raw_matches JSON-fields of all
    DocumentReports from MSGraph calendar events, then set the "start" 
    property, if one is not already set."""

    DocumentReport = apps.get_model("os2datascanner_report", "DocumentReport")

    msgraph_calendar_reports = DocumentReport.objects.filter(source_type="msgraph-calendar")

    for report in msgraph_calendar_reports.iterator():
        if not report.raw_metadata["handle"].get("start", None):
            report.raw_metadata["handle"]["start"] = "null"
        if not report.raw_matches["handle"].get("start", None):
            report.raw_matches["handle"]["start"] = "null"
        report.save()

class Migration(migrations.Migration):

    dependencies = [
        ('os2datascanner_report', '0062_populate_missing_resolution_time_fields'),
    ]

    operations = [
        migrations.RunPython(add_start_to_calendar_reports, reverse_code=migrations.RunPython.noop),
    ]
