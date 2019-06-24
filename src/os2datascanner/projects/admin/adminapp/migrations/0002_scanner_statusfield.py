# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-06-14 09:33
from __future__ import unicode_literals

from django.db import migrations
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('os2datascanner', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='webscan',
            options={'verbose_name': 'Web report'},
        ),
        migrations.AddField(
            model_name='scan',
            name='creation_time',
            field=model_utils.fields.MonitorField(default=django.utils.timezone.now, monitor='status', verbose_name='Oprettelsestidspunkt', when=set(['NEW'])),
        ),
        migrations.AlterField(
            model_name='scan',
            name='end_time',
            field=model_utils.fields.MonitorField(default=None, monitor='status', null=True, verbose_name='Sluttidspunkt', when=set(['DONE', 'FAILED'])),
        ),
        migrations.AlterField(
            model_name='scan',
            name='start_time',
            field=model_utils.fields.MonitorField(default=None, monitor='status', null=True, verbose_name='Starttidspunkt', when=set(['STARTED'])),
        ),
        migrations.AlterField(
            model_name='scan',
            name='status',
            field=model_utils.fields.StatusField(choices=[(0, 'dummy')], default='NEW', max_length=9, no_check_for_status=True),
        ),
    ]