#!/usr/bin/env python
# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2datascanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (https://os2.eu/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( https://os2.eu/ )

from django.core.management.base import BaseCommand

from os2datascanner.utils.system_utilities import parse_isoformat_timestamp
from os2datascanner.engine2.rules.last_modified import LastModifiedRule
from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.pipeline.utilities.pika import PikaPipelineRunner
from os2datascanner.projects.report.reportapp.utils import hash_handle

from ...models.documentreport_model import DocumentReport


def message_received_raw(queue, body):
    """Method for restructuring and storing result body.

    The agreed structure is as follows:
    {'scan_tag': {...}, 'matches': null, 'metadata': null, 'problem': null}
    """
    reference = body.get("handle") or body.get("source")
    tag, queue = _identify_message(body)
    if not reference or not tag or not queue:
        return

    previous_report, new_report = get_reports_for(reference, tag)
    if queue == "matches":
        handle_match_message(previous_report, new_report, body)
    elif queue == "problem":
        handle_problem_message(previous_report, new_report, body)
    elif queue == "metadata":
        new_report.data["metadata"] = body
        new_report.save()

    yield from []


def get_reports_for(reference, scan_tag):
    scanner = scan_tag["scanner"]
    time_raw = scan_tag["time"]
    time = parse_isoformat_timestamp(time_raw)

    path = hash_handle(reference)
    previous_report = DocumentReport.objects.filter(path=path,
            data__scan_tag__scanner=scanner).order_by("-scan_time").first()
    # get_or_create unconditionally writes freshly-created objects to the
    # database (in the version of Django we're using at the moment, at least),
    # so we have to implement similar logic ourselves
    try:
        new_report = DocumentReport.objects.filter(
                path=path, scan_time=time).get()
    except DocumentReport.DoesNotExist:
        new_report = DocumentReport(path=path, scan_time=time,
                data={"scan_tag": scan_tag})

    return previous_report, new_report


def handle_match_message(previous_report, new_report, body):
    new_matches = messages.MatchesMessage.from_json_object(body)
    previous_matches = previous_report.matches if previous_report else None

    if previous_report and previous_report.resolution_status is None:
        # There are existing unresolved results; resolve them based on the new
        # message
        if previous_matches:
            if not new_matches.matched:
                # No new matches. Be cautiously optimistic, but check what
                # actually happened
                if (len(new_matches.matches) == 1
                        and isinstance(new_matches.matches[0].rule,
                                LastModifiedRule)):
                    # The file hasn't been changed, so the matches are the same
                    # as they were last time. Instead of making a new entry,
                    # just update the timestamp on the old one
                    print(new_matches.handle.presentation,
                            "LM/no change, updating timestamp")
                    previous_report.scan_time = parse_isoformat_timestamp(
                            new_matches.scan_spec.scan_tag["time"])
                    previous_report.save()
                else:
                    # The file has been edited and the matches are no longer
                    # present
                    print(new_matches.handle.presentation,
                            "Changed, no matches, old status is now EDITED")
                    previous_report.resolution_status = (
                            DocumentReport.ResolutionChoices.EDITED.value)
                    previous_report.save()
            else:
                # The file has been edited, but matches are still present.
                # Resolve the previous ones
                print(new_matches.handle.presentation,
                        "Changed, new matches, old status is now EDITED")
                previous_report.resolution_status = (
                        DocumentReport.ResolutionChoices.EDITED.value)
                previous_report.save()

    if new_matches.matched:
        print(new_matches.handle.presentation, "New matches, creating")
        new_report.data["matches"] = body
        new_report.save()


def handle_problem_message(previous_report, new_report, body):
    problem = messages.ProblemMessage.from_json_object(body)
    if (previous_report and previous_report.resolution_status is None
            and problem.missing):
        # The file previously had matches, but has been removed. Resolve them
        print(problem.handle.presentation if problem.handle else "(source)",
                "Problem, deleted, old status is now REMOVED")
        previous_report.resolution_status = (
                DocumentReport.ResolutionChoices.REMOVED.value)
        previous_report.save()
    else:
        print(problem.handle.presentation if problem.handle else "(source)",
                "Problem, transient, creating")
        new_report.data["problem"] = body
        new_report.save()


def _identify_message(result):
    origin = result.get('origin')

    if origin == 'os2ds_problems':
        return (result.get("scan_tag"), "problem")
    elif origin == 'os2ds_metadata':
        return (result.get("scan_tag"), "metadata")
    elif origin == "os2ds_matches":
        return (result["scan_spec"].get("scan_tag"), "matches")
    else:
        return None, None


class ReportCollector(PikaPipelineRunner):
    def handle_message(self, message_body, *, channel=None):
        return message_received_raw(channel, message_body)


class Command(BaseCommand):
    """Command for starting a pipeline collector process."""
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "--results",
            type=str,
            help="the name of the AMQP queue from which filtered result objects"
                 + " should be read",
            default="os2ds_results")

    def handle(self, results, *args, **options):
        with ReportCollector(read=[results], heartbeat=6000) as runner:
            try:
                print("Start")
                runner.run_consumer()
            finally:
                print("Stop")
