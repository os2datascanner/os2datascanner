# Generated by Django 2.2.4 on 2020-01-07 10:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('os2datascanner', '0017_track_scanner_start'),
    ]

    operations = [
        migrations.AddField(
            model_name='exchangescanner',
            name='service_endpoint',
            field=models.URLField(max_length=256, null=True, verbose_name='Service endpoint'),
        ),
    ]



