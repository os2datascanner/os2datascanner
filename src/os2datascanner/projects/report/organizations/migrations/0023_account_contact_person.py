# Generated by Django 3.2.11 on 2023-08-28 06:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0022_organization_dpotab_access'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='contact_person',
            field=models.BooleanField(default=False, verbose_name='Contact person'),
        ),
    ]
