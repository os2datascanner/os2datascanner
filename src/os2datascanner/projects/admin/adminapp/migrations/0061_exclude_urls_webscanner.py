# Generated by Django 3.2.4 on 2021-07-29 07:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('os2datascanner', '0060_filescanner_super_hidden'),
    ]

    operations = [
        migrations.AddField(
            model_name='webscanner',
            name='exclude_urls',
            field=models.CharField(blank=True, default='', max_length=2048, verbose_name='exclude urls'),
        ),
    ]
