# Generated by Django 2.2.18 on 2021-04-26 16:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0002_alias'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='imported',
            field=models.BooleanField(default=False, editable=False, verbose_name='has been imported'),
        ),
        migrations.AddField(
            model_name='account',
            name='imported_id',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name='imported unique ID'),
        ),
        migrations.AddField(
            model_name='account',
            name='last_import',
            field=models.DateTimeField(blank=True, null=True, verbose_name='last successful import'),
        ),
        migrations.AddField(
            model_name='account',
            name='last_import_requested',
            field=models.DateTimeField(blank=True, null=True, verbose_name='last time an update was requested'),
        ),
        migrations.AddField(
            model_name='alias',
            name='imported',
            field=models.BooleanField(default=False, editable=False, verbose_name='has been imported'),
        ),
        migrations.AddField(
            model_name='alias',
            name='imported_id',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name='imported unique ID'),
        ),
        migrations.AddField(
            model_name='alias',
            name='last_import',
            field=models.DateTimeField(blank=True, null=True, verbose_name='last successful import'),
        ),
        migrations.AddField(
            model_name='alias',
            name='last_import_requested',
            field=models.DateTimeField(blank=True, null=True, verbose_name='last time an update was requested'),
        ),
        migrations.AddField(
            model_name='organizationalunit',
            name='imported',
            field=models.BooleanField(default=False, editable=False, verbose_name='has been imported'),
        ),
        migrations.AddField(
            model_name='organizationalunit',
            name='imported_id',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name='imported unique ID'),
        ),
        migrations.AddField(
            model_name='organizationalunit',
            name='last_import',
            field=models.DateTimeField(blank=True, null=True, verbose_name='last successful import'),
        ),
        migrations.AddField(
            model_name='organizationalunit',
            name='last_import_requested',
            field=models.DateTimeField(blank=True, null=True, verbose_name='last time an update was requested'),
        ),
        migrations.AddField(
            model_name='position',
            name='imported',
            field=models.BooleanField(default=False, editable=False, verbose_name='has been imported'),
        ),
        migrations.AddField(
            model_name='position',
            name='imported_id',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name='imported unique ID'),
        ),
        migrations.AddField(
            model_name='position',
            name='last_import',
            field=models.DateTimeField(blank=True, null=True, verbose_name='last successful import'),
        ),
        migrations.AddField(
            model_name='position',
            name='last_import_requested',
            field=models.DateTimeField(blank=True, null=True, verbose_name='last time an update was requested'),
        ),
    ]



