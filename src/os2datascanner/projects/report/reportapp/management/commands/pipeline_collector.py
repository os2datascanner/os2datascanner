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
import logging
import structlog

from django.db import DataError, transaction
from django.db.models.deletion import ProtectedError
from django.core.management.base import BaseCommand
from django.core.exceptions import FieldError

from os2datascanner.engine2.rules.last_modified import LastModifiedRule
from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.pipeline.run_stage import _loglevels
from os2datascanner.engine2.pipeline.utilities.pika import PikaPipelineThread
from os2datascanner.engine2.conversions.types import OutputType
from os2datascanner.engine2.model.core import Handle, Source
from os2datascanner.utils.system_utilities import time_now

from prometheus_client import Summary, start_http_server

from ...models.documentreport_model import DocumentReport
from ...models.organization_model import Organization
from ...utils import hash_handle, prepare_json_object

logger = structlog.get_logger(__name__)
SUMMARY = Summary("os2datascanner_pipeline_collector_report",
                  "Messages through report collector")


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

    # XXX: ideally we would only log once in this file. When all is done, log the
    # following AND what actions were taken.
    logger.debug(
        "msg received",
        queue=queue,
        tag=tag.scanner.to_json_object(),
        handle=Handle.from_json_object(reference).censor().to_json_object()
        if body.get("handle") else None,
        source=Source.from_json_object(reference).censor().to_json_object()
        if not body.get("handle") else None,
        prev_report=previous_report,
    )

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
        logger.debug("event_message_received_raw:"
                     f" unknown model_class {model_class} in event")
        return

    yield from []


def handle_metadata_message(new_report, result):
    message = messages.MetadataMessage.from_json_object(result)

    new_report.raw_metadata = result
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
    logger.debug("updating timestamp", report=new_report.presentation)
    new_report.scanner_job_name = message.scan_tag.scanner.name
    save_if_path_and_scanner_job_pk_unique(new_report, message.scan_tag.scanner.pk)


def get_reports_for(reference, scan_tag: messages.ScanTagFragment):
    path = hash_handle(reference)
    scanner_json = scan_tag.scanner.to_json_object()
    previous_report = DocumentReport.objects.filter(
        path=path,
        raw_scan_tag__scanner=scanner_json).order_by("-scan_time").first()
    # get_or_create unconditionally writes freshly-created objects to the
    # database (in the version of Django we're using at the moment, at least),
    # so we have to implement similar logic ourselves
    try:
        new_report = DocumentReport.objects.filter(
                path=path, scan_time=scan_tag.time,
                raw_scan_tag=scan_tag.to_json_object()).get()
    except DocumentReport.DoesNotExist:
        new_report = DocumentReport(
            path=path, scan_time=scan_tag.time,
            raw_scan_tag=scan_tag.to_json_object())

    return previous_report, new_report


def handle_match_message(previous_report, new_report, body):  # noqa: CCR001, E501 too high cognitive complexity
    new_matches = messages.MatchesMessage.from_json_object(body)
    previous_matches = previous_report.matches if previous_report else None

    matches = [(match.rule.presentation, match.matches) for match in new_matches.matches]
    logger.debug(
        "new matchMsg",
        handle=new_matches.handle.presentation,
        msgtype="matches",
        matches=matches,
    )
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
                    logger.debug("Resource not changed: updating scan timestamp",
                                 report=previous_report)
                    previous_report.scan_time = (
                            new_matches.scan_spec.scan_tag.time)
                    previous_report.save()
                else:
                    # The file has been edited and the matches are no longer
                    # present
                    logger.debug("Resource changed: no matches, status is EDITED",
                                 report=previous_report)
                    previous_report.resolution_status = (
                            DocumentReport.ResolutionChoices.EDITED.value)
                    previous_report.save()
            else:
                # The file has been edited, but matches are still present.
                # Resolve the previous ones
                logger.debug("matches still present, status is EDITED",
                             report=previous_report)
                previous_report.resolution_status = (
                        DocumentReport.ResolutionChoices.EDITED.value)
                previous_report.save()

    if new_matches.matched:

        # Collect and store the top-level type label from the matched object
        source = new_matches.handle.source
        while source.handle:
            source = source.handle.source
        new_report.source_type = source.type_label
        new_report.name = new_matches.handle.presentation_name
        new_report.sort_key = new_matches.handle.sort_key

        # Collect and store highest sensitivity value (should never be NoneType).
        new_report.sensitivity = new_matches.sensitivity.value
        # Collect and store highest propability value (should never be NoneType).
        new_report.probability = new_matches.probability
        # Sort matches by prop. desc.
        new_report.raw_matches = sort_matches_by_probability(body)
        new_report.scanner_job_name = new_matches.scan_spec.scan_tag.scanner.name

        save_if_path_and_scanner_job_pk_unique(
            new_report, new_matches.scan_spec.scan_tag.scanner.pk)

        logger.debug("matches, saving new DocReport", report=new_report)
    elif new_report is not None:
        logger.debug("No new matches.")


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

    handle = problem.handle if problem.handle else None
    presentation = handle.presentation if handle else "(source)"
    if (previous_report and previous_report.resolution_status is None
            and problem.missing):
        # The file previously had matches, but is now removed.
        logger.debug(
            "Resource deleted, status is REMOVED",
            report=previous_report,
            handle=presentation,
            msgtype="problem",
        )
        previous_report.resolution_status = (
                DocumentReport.ResolutionChoices.REMOVED.value)
        previous_report.save()
    else:

        # Collect and store the top-level type label from the failing object
        source = problem.handle.source if problem.handle else problem.source
        while source.handle:
            source = source.handle.source

        new_report.source_type = source.type_label
        new_report.name = handle.presentation_name if handle else ""
        new_report.sort_key = handle.sort_key if handle else "(source)"
        new_report.raw_problem = body
        new_report.scanner_job_name = problem.scan_tag.scanner.name

        save_if_path_and_scanner_job_pk_unique(new_report, problem.scan_tag.scanner.pk)

        logger.debug(
            "Unresolved, saving new report",
            report=new_report,
            handle=presentation,
            msgtype="problem",
        )


def _identify_message(result):
    origin = result.get('origin')

    if origin == 'os2ds_problems':
        return result.get("scan_tag"), "problem"
    elif origin == 'os2ds_metadata':
        return result.get("scan_tag"), "metadata"
    elif origin == "os2ds_matches":
        return result["scan_spec"].get("scan_tag"), "matches"
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
            logger.debug(f"handle_event: deleted {cn} {existing.uuid}")
            existing.delete()
        elif event_type == "object_update":
            existing.__dict__.update(instance_fields)
            existing.save()
            logger.debug(f"handle_event: updated {cn} {existing.uuid}")
        else:
            logger.warning("handle_event: unexpected event_type"
                           f" {event_type} for {cn} {existing.uuid}")

    except cls.DoesNotExist:
        # The object didn't exist -- save it. Note that we might also end up
        # here with an update event if the initial create event didn't get
        # propagated over to the report module
        event_obj.save()
        logger.debug(f"handle_event: created {cn} {event_obj.uuid}")
    except FieldError as e:
        logger.debug(f"handle_event: FieldError when handling {cn}: {e}")
    except AttributeError as e:
        logger.debug(f"handle_event: AttributeError when handling {cn}: {e}")
    except ProtectedError as e:
        logger.debug(
                f"handle_event: couldn't delete {cn} {event_obj.uuid}: {e}")


def save_if_path_and_scanner_job_pk_unique(new_report, scanner_job_pk):
    """
      If a DocumentReport with scanner_job_pk and path already exists,
      then creating a new one will violate path and scanner_job_pk unique constraint.

      Therefore we check if one already exist, delete it if so, and then we create a new one.
    """
    try:
        existing_report = DocumentReport.objects.filter(
            scanner_job_pk=scanner_job_pk,
            path=new_report.path
        ).get()

        existing_report.delete()
    except DocumentReport.DoesNotExist:
        pass

    new_report.scanner_job_pk = scanner_job_pk
    try:
        with transaction.atomic():
            new_report.save()
    except (DataError, UnicodeEncodeError):
        # To the best of our knowledge, this can only happen if we try to store
        # a null byte in a PostgreSQL text field (or something that's related
        # to a text field, like the JSON field types). Edit these bytes out and
        # try again
        for field in ("raw_scan_tag", "raw_matches",
                "raw_problem", "raw_metadata", "sort_key", "name"):
            setattr(new_report, field,
                    prepare_json_object(getattr(new_report, field)))
        new_report.save()


class CollectorRunner(PikaPipelineThread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        start_http_server(9091)

    def handle_message(self, routing_key, body):
        with SUMMARY.time():
            logger.debug(
                "raw message received",
                routing_key=routing_key,
                body=body)
            if routing_key == "os2ds_results":
                yield from result_message_received_raw(body)
            elif routing_key == "os2ds_events":
                yield from event_message_received_raw(body)


class Command(BaseCommand):
    """Command for starting a pipeline collector process."""
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
                "--log",
                default="info",
                help="change the level at which log messages will be printed",
                choices=_loglevels.keys())

    def handle(self, *args, log, **options):
        # change formatting to include datestamp
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(format=fmt, datefmt='%Y-%m-%d %H:%M:%S')
        # set level for root logger
        logging.getLogger("os2datascanner").setLevel(_loglevels[log])

        CollectorRunner(
                exclusive=True,
                read=["os2ds_results", "os2ds_events"],
                prefetch_count=8).run_consumer()
