# Generated by Django 2.2.10 on 2020-07-13 14:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('os2datascanner', '0031_merge_20200707_1142'),
    ]

    operations = [
        migrations.CreateModel(
            name='MSGraphFileScanner',
            fields=[
                ('scanner_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='os2datascanner.Scanner')),
                ('tenant_id', models.CharField(max_length=256, verbose_name='Tenant ID')),
                ('scan_site_drives', models.BooleanField(default=True, verbose_name='Scan alle SharePoint-mapper')),
                ('scan_user_drives', models.BooleanField(default=True, verbose_name='Scan alle OneDrive-drev')),
            ],
            options={
                'abstract': False,
            },
            bases=('os2datascanner.scanner',),
        ),
    ]



