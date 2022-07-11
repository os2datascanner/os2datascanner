# Generated by Django 3.2.11 on 2022-03-10 12:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('os2datascanner', '0072_scan_status_added_default_values'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='scanstatus',
            index=models.Index(fields=['scanner', 'scan_tag'], name='ss_pc_lookup'),
        ),
        # Prior to version 3.15.0, this migration also created an index based
        # on ScheduledCheckup's handle_representation field, but that produced
        # migration failures in production, as that field is often too big to
        # index. Dummying out this part of the migration lets us finish the
        # production deployments, and migration 0081 should get everybody back
        # in sync
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddIndex(
                    model_name='scheduledcheckup',
                    index=models.Index(fields=['scanner', 'handle_representation'], name='sc_pc_lookup'),
                ),
            ],
            database_operations=[]
        ),
    ]
