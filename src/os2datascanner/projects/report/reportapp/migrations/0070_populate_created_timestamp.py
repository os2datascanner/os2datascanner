from django.db import migrations, models
from django.db.models import F, Q
from django.utils import timezone

def populate_created_timestamp(apps, schema_editor):
    """We have seen cases where created_timestamp was not set correctly,
    due to previously broken logic. As a temporary solution, the
    created_timestamp of these reports were set to 1/1 2015, to make other
    logic depending on this field work. This migration sets the field
    to the time the scan was run, for a better estimation."""

    DocumentReport = apps.get_model("os2datascanner_report", "DocumentReport")

    drs = DocumentReport.objects.filter(
        Q(created_timestamp=timezone.make_aware(timezone.datetime(2015, 1, 1, 0, 0)))|
        Q(created_timestamp__isnull=True))

    drs.update(created_timestamp=F("scan_time"))

class Migration(migrations.Migration):
    dependencies = [
        ("os2datascanner_report", "0069_alter_path_field_new_transaction"),
    ]

    operations = [
        migrations.RunPython(populate_created_timestamp, reverse_code=migrations.RunPython.noop),
    ]