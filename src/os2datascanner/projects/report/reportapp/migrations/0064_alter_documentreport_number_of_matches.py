# Generated by Django 3.2.11 on 2023-02-02 09:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('os2datascanner_report', '0063_alter_path_on_document_reports'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentreport',
            name='number_of_matches',
            field=models.IntegerField(db_index=True, default=0, verbose_name='number of matches'),
        ),
    ]
