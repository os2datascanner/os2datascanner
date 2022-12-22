from django.db import migrations, models
from django.db.models.query_utils import Q
from django.utils import timezone

def populate_resolution_time(apps, schema_editor):
    """Set the resolution_time of all resolved DocumentReports without one to 
    7 days after the report was created. All reports with a resolution time of 
    exactly 00:00 on the 2nd december of 2022 are all temporary 
    resolution_times, so these are changed as well."""

    DocumentReport = apps.get_model("os2datascanner_report", "DocumentReport")

    temp_date = timezone.make_aware(timezone.datetime(year=2022, month=12, day=2, hour=0, minute=0))

    now = timezone.now()

    dr = DocumentReport.objects.filter(Q(resolution_status__isnull=False, resolution_time__isnull=True)|
                                       Q(resolution_status__isnull=False, resolution_time=temp_date))

    for report in dr.iterator():
        new_date = report.scan_time + timezone.timedelta(days=7)
        report.resolution_time = min([new_date, now])
        report.save()


class Migration(migrations.Migration):

    dependencies = [
        ('os2datascanner_report', '0061_dataprotectionofficer_contact_person'),
    ]

    operations = [
        migrations.RunPython(populate_resolution_time, reverse_code=migrations.RunPython.noop),
    ]
