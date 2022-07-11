# Generated by Django 2.2.10 on 2020-04-29 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('os2datascanner_report', '0008_webdomainalias'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentreport',
            name='custom_resolution_status',
            field=models.CharField(blank=True, max_length=1024, verbose_name='Begrundelse'),
        ),
        migrations.AddField(
            model_name='documentreport',
            name='resolution_status',
            field=models.IntegerField(blank=True, choices=[(0, 'Andet'), (1, 'Redigeret'), (2, 'Flyttet'), (3, 'Slettet')], null=True, verbose_name='Håndteringsstatus'),
        ),
    ]



