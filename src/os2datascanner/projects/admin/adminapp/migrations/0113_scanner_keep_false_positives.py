# Generated by Django 3.2.11 on 2023-10-31 13:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('os2datascanner', '0112_turbohealthrule'),
    ]

    operations = [
        migrations.AddField(
            model_name='scanner',
            name='keep_false_positives',
            field=models.BooleanField(default=True, verbose_name='keep false positives'),
        ),
    ]
