from django.db import migrations, models

class Migration(migrations.Migration):

  dependencies = [
        ('os2datascanner_report', '0068_alter_documentreport_path'),
    ]

  operations = [
    migrations.AlterField(
            model_name='documentreport',
            name='path',
            field=models.CharField(max_length=256, verbose_name='path'),
        ),
        migrations.RemoveIndex(
            model_name='documentreport',
            name='pc_update_query',
        ),
        migrations.AddIndex(
            model_name='documentreport',
            index=models.Index(fields=['path'], name='pc_update_query'),
        ),
  ]