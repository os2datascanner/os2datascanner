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
from django.core.exceptions import FieldError
from django.db.models.deletion import ProtectedError

from os2datascanner.utils.system_utilities import parse_isoformat_timestamp
from os2datascanner.engine2.rules.last_modified import LastModifiedRule
from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.pipeline.utilities.pika import PikaPipelineRunner
from os2datascanner.projects.report.reportapp.utils import hash_handle

from ...models.documentreport_model import DocumentReport
from ...models.organization_model import Organization


def result_message_received_raw(body):
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
        handle_metadata_message(new_report, body)

    yield from []


def event_message_received_raw(body):
    event_type = body.get("type")
    model_class = body.get("model_class")
    instance = body.get("instance")

    if not event_type or not model_class or not instance:
        return

    if model_class == "Organization":
        handle_event(event_type, instance, Organization)
    else:
        print("Unknown model_class %s in event" % model_class)
        return

    yield from []


def handle_metadata_message(new_report, result):
    new_report.data["metadata"] = result
    new_report.save()


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
        # Collect and store highest sensitivity value (should never be NoneType).
        new_report.sensitivity = new_matches.sensitivity.value
        # Collect and store highest propability value (should never be NoneType).
        new_report.probability = new_matches.probability
        # Sort matches by prop. desc.
        new_report.data["matches"] = sort_matches_by_probability(body)
        new_report.save()


def sort_matches_by_probability(body):
    """The scanner engine have some internal rules
    and the matches they produce are also a part of the message.
    These matches are not necessary in the report module.
    An example of an internal rule is, images below a certain size are
    ignored."""

    # Rules are under no obligation to produce matches in any
    # particular order, but we want to display them in
    # descending order of probability
    for match_fragment in body["matches"]:
        if match_fragment["matches"]:
            match_fragment["matches"].sort(
                key=lambda match_dict: match_dict.get(
                    "probability", 0.0),
                reverse=True)
    return body


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


def handle_event(event_type, instance, cls):

    event_obj = cls.from_json_object(instance)

    try:
        existing = cls.objects.get(uuid=event_obj.uuid)

        # If we get this far, the object existed
        # go ahead and update or delete
        if event_type == "object_delete":
            existing.delete()
            print("handle_event: Deleted %s with uuid: %s" % (cls, existing.uuid))
        elif event_type == "object_update":
            event_obj_dict = {k: v for k, v in event_obj.__dict__.items() if v is not None}
            existing.__dict__.update(event_obj_dict)
            existing.save()
            print("handle_event: Updated %s with uuid: %s" % (cls, existing.uuid))
        else:
            print("handle_event: Unexpected event_type %s from %s with uuid: %s" % (event_type, cls, event_obj.uuid))

    except cls.DoesNotExist:
        # The object didn't exist - save it
        # Notice that we might end up here event with an update event, if the initial
        # create event wasn't created, collected or didn't succeed
        event_obj.save()
        print("handle_event: Created %s with uuid: %s" % (cls, event_obj.uuid))
    except FieldError as e:
        print("handle_event: FieldError when handling %s from event: %s" % (cls, e))
    except AttributeError as e:
        print("handle_event: AttributeError when handling %s from event: %s" % (cls, e))
    except ProtectedError as e:
        print("handle_event: Couldn't delete %s uuid %s from event: %s" % (cls, event_obj.uuid, e))


class ReportCollector(PikaPipelineRunner):
    def handle_message(self, message_body, *, channel=None):
        if channel == "os2ds_results":
            return result_message_received_raw(message_body)
        elif channel == "os2ds_events":
            return event_message_received_raw(message_body)


class Command(BaseCommand):
    """Command for starting a pipeline collector process."""
    help = __doc__

    def handle(self, *args, **options):
        with ReportCollector(
                read=["os2ds_results", "os2ds_events"], heartbeat=6000) as runner:
            try:
                print("Start")
                runner.run_consumer(exclusive=True)
            finally:
                print("Stop")
