from django.conf import settings
from django.db import migrations
from django.db.models import F
from os2datascanner.projects.admin.core.models.client import Scan

def update_scantypes(apps, schema_editor):
    """This migration adds an new filescan option, which can be toggled. 
    The value of the settings-file determines whether or not MSGraph Teams filescan is shown to the user as default."""
    Client = apps.get_model("core", "Client")

    Client.objects.all().update(scans=F("scans") + (Scan.MSGRAPH_TEAMS_FILESCAN.value if settings.ENABLE_MSGRAPH_TEAMS_FILESCAN else 0))


class Migration(migrations.Migration):

    dependencies = [
        ('os2datascanner', '0109_alter_scanstatussnapshot_scan_status'),
    ]

    operations = [
        migrations.RunPython(update_scantypes,
                             reverse_code=migrations.RunPython.noop),
    ]
