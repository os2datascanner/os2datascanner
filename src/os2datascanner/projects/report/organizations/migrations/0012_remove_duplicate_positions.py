from django.db import migrations, models
from django.db.models import Count

def remove_duplicate_positions(apps, schema_editor):
    Position = apps.get_model("organizations", "Position")

    duplicates = Position.objects.values("account", "unit", "role").annotate(count=Count("pk")).filter(count__gt=1)

    for position in duplicates:
        positions = Position.objects.filter(account=position.get("account"), unit=position.get("unit"), role=position.get("role"))

        to_keep = positions.first()
        positions.exclude(pk=to_keep.pk).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0011_add_matchcount_and_matchstatus_to_account'),
    ]

    operations = [
        migrations.RunPython(
            remove_duplicate_positions, reverse_code=migrations.RunPython.noop
        )
    ]
