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

import json

from django.core.management.base import BaseCommand
from django.core.exceptions import FieldError
from django.db.models.deletion import ProtectedError

from os2datascanner.utils.system_utilities import (
        time_now, parse_isoformat_timestamp)
from os2datascanner.engine2.rules.last_modified import LastModifiedRule
from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.pipeline.utilities.pika import PikaPipelineThread
from os2datascanner.projects.report.reportapp.utils import hash_handle
from os2datascanner.engine2.conversions.types import OutputType
from ...models.documentreport_model import DocumentReport
from ...models.organization_model import Organization

import structlog
logger = structlog.get_logger(__name__)


def result_message_received_raw(body):
    """Method for restructuring and storing result body.

    The agreed structure is as follows:
    {'scan_tag': {...}, 'matches': null, 'metadata': null, 'problem': null}
    """
    reference = body.get("handle") or body.get("source")
    tag, queue = _identify_message(body)
    if not reference or not tag or not queue:
        return
    tag = messages.ScanTagFragment.from_json_object(tag)

    previous_report, new_report = get_reports_for(reference, tag)

    # if presentation=="", then it is a new report still not updated with the
    # recieved Message
    new_presentation = new_report.presentation
    prev_presentation = previous_report.presentation if previous_report else ""
    logger.info(f"Message recieved from queue {queue}")
    if prev_presentation:
        logger.info(f"previous {previous_report} for {prev_presentation}")
    else:
        logger.info("No previous report")
    if new_presentation:
        logger.info(f"new {new_report} for {new_report.presentation}")
    else:
        logger.info(f"new report created but still not saved")

    if queue == "matches":
        handle_match_message(previous_report, new_report, body)
    elif queue == "problem":
        handle_problem_message(previous_report, new_report, body)
    elif queue == "metadata":
        handle_metadata_message(new_report, body)
    # newline in logs, to indicate handling is done
    print()

    yield from []


def event_message_received_raw(body):
    event_type = body.get("type")
    model_class = body.get("model_class")
    instance = body.get("instance")

    if not event_type or not model_class or not instance:
        return

    # Version 3.9.0 switched to using django.core.serializers for
    # ModelChangeEvent messages and so has a completely different wire format.
    # Rather than attempting to handle both, we detect messages from older
    # versions and drop them on the floor
    if not (isinstance(instance, str)
            and instance.startswith("[") and instance.endswith("]")):
        logger.warning("Ignoring old-style ModelChangeEvent")
        return
    else:
        instance = json.loads(instance)[0]

    if model_class == "Organization":
        handle_event(event_type, instance, Organization)
    else:
        logger.info("event_message_received_raw:"
                f" unknown model_class {model_class} in event")
        return

    yield from []


def handle_metadata_message(new_report, result):
    message = messages.MetadataMessage.from_json_object(result)

    new_report.data["metadata"] = result
    if "last-modified" in message.metadata:
        new_report.datasource_last_modified = (
                OutputType.LastModified.decode_json_object(
                        message.metadata["last-modified"]))
    else:
        # If no scan_tag time is found, default value to current time as this
        # must be some-what close to actual scan_tag time.
        # If no datasource_last_modified value is ever set, matches will not be
        # shown.
        new_report.datasource_last_modified = (
                message.scan_tag.time or time_now())
    logger.info(f"updating timestamp for {new_report.presentation}")
    new_report.save()


def get_reports_for(reference, scan_tag: messages.ScanTagFragment):
    path = hash_handle(reference)
    scanner_json = scan_tag.scanner.to_json_object()
    previous_report = DocumentReport.objects.filter(path=path,
            data__scan_tag__scanner=scanner_json).order_by(
            "-scan_time").first()
    # get_or_create unconditionally writes freshly-created objects to the
    # database (in the version of Django we're using at the moment, at least),
    # so we have to implement similar logic ourselves
    try:
        new_report = DocumentReport.objects.filter(
                path=path, scan_time=scan_tag.time).get()
    except DocumentReport.DoesNotExist:
        new_report = DocumentReport(path=path, scan_time=scan_tag.time,
                data={"scan_tag": scan_tag.to_json_object()})

    return previous_report, new_report


def handle_match_message(previous_report, new_report, body):
    new_matches = messages.MatchesMessage.from_json_object(body)
    previous_matches = previous_report.matches if previous_report else None

    matches = [(match.rule.presentation, match.matches) for match in new_matches.matches]
    logger.info(f"{new_matches.handle.presentation} has the matches: {matches}")
    if previous_report and previous_report.resolution_status is None:
        # There are existing unresolved results; resolve them based on the new
        # message
        if previous_matches:
            logger.info("There is a previous match for the file. "
                        f"Updating {previous_report} by doing")
            if not new_matches.matched:
                # No new matches. Be cautiously optimistic, but check what
                # actually happened
                if (len(new_matches.matches) == 1
                        and isinstance(new_matches.matches[0].rule,
                                LastModifiedRule)):
                    # The file hasn't been changed, so the matches are the same
                    # as they were last time. Instead of making a new entry,
                    # just update the timestamp on the old one
                    logger.info("File not changed: updating LastModified timestamp")
                    previous_report.scan_time = (
                            new_matches.scan_spec.scan_tag.time)
                    previous_report.save()
                else:
                    # The file has been edited and the matches are no longer
                    # present
                    logger.info("File changed: no matches, status is now EDITED")
                    previous_report.resolution_status = (
                            DocumentReport.ResolutionChoices.EDITED.value)
                    previous_report.save()
            else:
                # XXX How do we know its been edited? This is hit whenever there's a match
                # The file has been edited, but matches are still present.
                # Resolve the previous ones
                logger.info("Matches still present, status is now EDITED."
                            "A new report will be created")
                previous_report.resolution_status = (
                        DocumentReport.ResolutionChoices.EDITED.value)
                previous_report.save()

    if new_matches.matched:

        # Collect and store the top-level type label from the matched object
        source = new_matches.handle.source
        while source.handle:
            source = source.handle.source
        new_report.source_type = source.type_label

        # Collect and store highest sensitivity value (should never be NoneType).
        new_report.sensitivity = new_matches.sensitivity.value
        # Collect and store highest propability value (should never be NoneType).
        new_report.probability = new_matches.probability
        # Sort matches by prop. desc.
        new_report.data["matches"] = sort_matches_by_probability(body)
        new_report.save()
        logger.info(f"Matches: Saving new {new_report}")
    else:
        logger.info(f"No new matches. {new_report} not saved")


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

    presentation = problem.handle.presentation if problem.handle else "(source)"
    logger.info(f"ProblemMessage for {presentation}")
    if (previous_report and previous_report.resolution_status is None
            and problem.missing):
        # The file previously had matches, but is now removed.
        logger.info(f"File deleted, previous {previous_report} set to REMOVED")
        previous_report.resolution_status = (
                DocumentReport.ResolutionChoices.REMOVED.value)
        previous_report.save()
    else:

        # Collect and store the top-level type label from the failing object
        source = problem.handle.source if problem.handle else problem.source
        while source.handle:
            source = source.handle.source
        new_report.source_type = source.type_label

        new_report.data["problem"] = body
        new_report.save()
        logger.info(f"Unresolved problem. Saving new {new_report}")

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
    cn = cls.__name__

    # We can't just go through django.core.serializers (not yet, anyway),
    # because the model classes are not actually shared between the admin
    # system and the report module. Instead, we copy the shared fields to a new
    # instance of the local model class
    class_field_names = tuple(f.name for f in cls._meta.fields)
    instance_fields = {
            k: v
            for k, v in instance["fields"].items()
            if k in class_field_names and v is not None}
    instance_fields["uuid"] = instance["pk"]
    event_obj = cls(**instance_fields)

    try:
        existing = cls.objects.get(uuid=event_obj.uuid)

        # If we get this far, the object existed
        # go ahead and update or delete
        if event_type == "object_delete":
            logger.info(f"handle_event: deleted {cn} {existing.uuid}")
            existing.delete()
        elif event_type == "object_update":
            existing.__dict__.update(instance_fields)
            existing.save()
            logger.info(f"handle_event: updated {cn} {existing.uuid}")
        else:
            logger.warning("handle_event: unexpected event_type"
                    f" {event_type} for {cn} {existing.uuid}")

    except cls.DoesNotExist:
        # The object didn't exist -- save it. Note that we might also end up
        # here with an update event if the initial create event didn't get
        # propagated over to the report module
        event_obj.save()
        logger.info(f"handle_event: created {cn} {event_obj.uuid}")
    except FieldError as e:
        logger.info(f"handle_event: FieldError when handling {cn}: {e}")
    except AttributeError as e:
        logger.info(f"handle_event: AttributeError when handling {cn}: {e}")
    except ProtectedError as e:
        logger.info(
                f"handle_event: couldn't delete {cn} {event_obj.uuid}: {e}")


class CollectorRunner(PikaPipelineThread):
    def handle_message(self, routing_key, body):
        if routing_key == "os2ds_results":
            return result_message_received_raw(body)
        elif routing_key == "os2ds_events":
            return event_message_received_raw(body)


class Command(BaseCommand):
    """Command for starting a pipeline collector process."""
    help = __doc__

    def handle(self, *args, **options):
        CollectorRunner(
            exclusive=True,
            read=["os2ds_results", "os2ds_events"],
        ).run_consumer()
