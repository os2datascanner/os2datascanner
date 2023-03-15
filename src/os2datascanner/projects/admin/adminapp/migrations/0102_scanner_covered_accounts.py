# Generated by Django 3.2.11 on 2023-03-17 11:43

from django.db import migrations, models


def populate_covered_accounts_field(apps, schema_editor):
    Scanner = apps.get_model("os2datascanner", "Scanner")
    for scanner in Scanner.objects.iterator():
        for org_unit in scanner.org_unit.iterator():
            scanner.covered_accounts.add(*org_unit.account_set.all())
            
class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0014_position_organizations_position_unique_constraint'),
        ('os2datascanner', '0101_webscanner_reduce_communication'),
    ]

    operations = [
        migrations.AddField(
            model_name='scanner',
            name='covered_accounts',
            field=models.ManyToManyField(blank=True, related_name='covered_by_scanner', to='organizations.Account', verbose_name='covered accounts'),
        ),
        migrations.RunPython(populate_covered_accounts_field, reverse_code=migrations.RunPython.noop)
    ]
