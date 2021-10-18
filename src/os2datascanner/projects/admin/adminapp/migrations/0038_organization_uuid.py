# Generated by Django 2.2.10 on 2020-11-18 07:12

from django.db import migrations, models
from uuid import uuid4


class Migration(migrations.Migration):

    dependencies = [
        ('os2datascanner', '0037_scanstatus'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='uuid',
            field=models.UUIDField(default=uuid4, editable=False, null=True),
        ),
    ]



