from django.core.management.base import BaseCommand
from os2datascanner.engine2.pipeline.messages import MetadataMessage, MatchesMessage, ProblemMessage

from ...models.documentreport_model import DocumentReport


class Command(BaseCommand):
    """ When run, updates every DocumentReport's sort_key value
    with it's handles current implementation of sort_key."""

    help = __doc__

    def handle(self, *args, **options):
        queryset = DocumentReport.objects.all()
        for report in queryset.iterator():
            try:
                handle = get_presentation(report)
                if not handle:
                    continue
                # ensure we don't try to put more chars into the db-fields than there's room for.
                # failing to do this will result in an django.db.DataError exception
                sort_key = handle.sort_key[:256]
                report.sort_key = sort_key
                report.save()

            except Exception as e:
                print(
                    f"Exception {type(e).__name__}\t"
                    f"report={report}\t"
                    f"e={e}"
                )
                raise
        self.stdout.write(self.style.SUCCESS("Refreshed sort keys!"))


def get_msg(query):
    # only one of these are not None
    matches = query.data.get("matches")
    metadata = query.data.get("metadata")
    problem = query.data.get("problem")

    if matches:
        return MatchesMessage.from_json_object(matches)
    elif problem:
        problem = ProblemMessage.from_json_object(problem)
        # problemMessage have optional handle and source fields. Try the latter if
        # the first is None.
        if not problem.handle:
            problem = problem.source if problem.source else problem
        return problem
    elif metadata:
        return MetadataMessage.from_json_object(metadata)
    else:
        return None


def get_presentation(query):
    """Get the handle"""

    type_msg = get_msg(query)
    if not type_msg:
        return ""

    return type_msg.handle if type_msg.handle else ""
