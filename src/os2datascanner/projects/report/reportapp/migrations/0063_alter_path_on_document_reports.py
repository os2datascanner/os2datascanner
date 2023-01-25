from django.db import migrations
from ..utils import crunch
from os2datascanner.engine2.pipeline.messages import MatchesMessage, ProblemMessage, MetadataMessage

def alter_path_field_on_document_reports(apps, _):
    """Change the path of DocumentReports to a string created with the
    'crunch'-function, instead of the 'hash_handle'-function."""

    DocumentReport = apps.get_model("os2datascanner_report", "DocumentReport")

    for dr in DocumentReport.objects.all().iterator():
        if dr.raw_matches:
            parent_object = MatchesMessage.from_json_object(dr.raw_matches)
        elif dr.raw_problem:
            parent_object = ProblemMessage.from_json_object(dr.raw_problem)
        elif dr.raw_metadata:
            parent_object = MetadataMessage.from_json_object(dr.raw_metadata)
        else:
            parent_object = None

        path = crunch(parent_object.handle if parent_object.handle else parent_object.source)

        if DocumentReport.objects.filter(scanner_job_pk=dr.scanner_job_pk, path=path).exists():
            dr.delete()
        else:
            dr.path = path
            dr.save()

class Migration(migrations.Migration):

  dependencies = [("os2datascanner_report", "0062_populate_missing_resolution_time_fields")]

  operations = [
    migrations.RunPython(alter_path_field_on_document_reports, reverse_code=migrations.RunPython.noop)
  ]