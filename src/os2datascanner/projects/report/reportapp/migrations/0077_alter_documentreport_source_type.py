# Generated by Django 3.2.11 on 2023-07-03 11:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('os2datascanner_report', '0076_alias_creation_index'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentreport',
            name='source_type',
            field=models.CharField(db_index=True, max_length=2000, verbose_name='source type'),
        ),
    ]
