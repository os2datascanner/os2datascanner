# Generated by Django 3.2.11 on 2023-03-17 13:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0013_position_organizations_position_unique_constraint'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='manager',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='managed_accounts', to='organizations.account'),
        ),
    ]
