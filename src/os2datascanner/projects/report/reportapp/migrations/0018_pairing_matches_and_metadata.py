# Generated by Django 2.2.10 on 2021-01-27 19:04

from django.db import migrations
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from ..utils import iterate_queryset_in_batches


def pairing_matches_and_metadata(apps, schema_editor):
    """This is a bugfix. Running multiple pipeline_collectors
    had the negative effect that messages from the scanner engine
    containing metadata did not get stored together with the matching match.
    This migration is given back matches their missing metadata."""
    DocumentReport = apps.get_model("os2datascanner_report", "DocumentReport")
    # find all matches that are missing metadata
    matches = DocumentReport.objects.filter(
        Q(data__matches__matched=True) &
        ~Q(data__icontains="os2ds_metadata"))

    print('\nNumber of Matches missing metadata {0}'.format(
        str(matches.count())))
    # find all metadata that are missing matches
    metadata = DocumentReport.objects.filter(
        Q(data__metadata__origin="os2ds_metadata") &
        ~Q(data__icontains='os2ds_matches'))

    print('\nNumber of Metadata missing matches {0}'.format(
        str(metadata.count())))

    for batch in iterate_queryset_in_batches(10000, matches):
        for match in batch:
            try:
                # find their missing partner and chain them together
                m_data = metadata.filter(scan_time=match.scan_time).get(path=match.path)
                match.data['metadata'] = m_data.data["metadata"]
            except ObjectDoesNotExist:
                print('No metadata for match with pk {0} exists'.format(
                    match.pk))
        DocumentReport.objects.bulk_update(batch, ['data'])

    metadata.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('os2datascanner_report', '0017_documentreport_added_sensitivity_and_probability'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='documentreport',
            options={'ordering': ['-sensitivity', '-probability'], 'verbose_name_plural': 'Document reports'},
        ),
        migrations.AlterModelOptions(
            name='remediator',
            options={'verbose_name': 'oprydder', 'verbose_name_plural': 'opryddere'},
        ),
        migrations.RunPython(pairing_matches_and_metadata,
                             reverse_code=migrations.RunPython.noop),
    ]
