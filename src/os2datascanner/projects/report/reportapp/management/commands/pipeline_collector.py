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

from django.db import transaction
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

from os2datascanner.projects.report.organizations.models import Organization

from prometheus_client import Summary, start_http_server

from ...models.documentreport_model import DocumentReport
from ...utils import hash_handle, prepare_json_object

from ...models.aliases.alias_model import Alias
from ...models.aliases.adsidalias_model import ADSIDAlias
from ...models.aliases.emailalias_model import EmailAlias
from ...models.aliases.webdomainalias_model import WebDomainAlias


logger = structlog.get_logger(__name__)
SUMMARY = Summary("os2datascanner_pipeline_collector_report",
                  "Messages through report collector")


def result_message_received_raw(body):
    """Method for restructuring and storing result body.

    The agreed structure is as follows:
    {'scan_tag': {...}, 'matches': null, 'metadata': null, 'problem': null}
    """
    reference = body.get("handle") or body.get("source")
    path = hash_handle(reference)
    tag, queue = _identify_message(body)
    if not reference or not tag or not queue:
        return
    tag = messages.ScanTagFragment.from_json_object(tag)

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
    )

    if queue == "matches":
        handle_match_message(path, tag, body)
    elif queue == "problem":
        handle_problem_message(path, tag, body)
    elif queue == "metadata":
        handle_metadata_message(path, tag, body)

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


def handle_metadata_message(path, scan_tag, result):
    # Evaluate the queryset that is updated later to lock it.
    DocumentReport.objects.select_for_update(
        of=('self',)
    ).filter(
        path=path,
        scanner_job_pk=scan_tag.scanner.pk
    ).first()

    message = messages.MetadataMessage.from_json_object(result)

    lm = None
    if "last-modified" in message.metadata:
        lm = OutputType.LastModified.decode_json_object(
                message.metadata["last-modified"])
    else:
        # If no scan_tag time is found, default value to current time as this
        # must be some-what close to actual scan_tag time.
        # If no datasource_last_modified value is ever set, matches will not be
        # shown.
        lm = scan_tag.time or time_now()

    dr, _ = DocumentReport.objects.update_or_create(
            path=path, scanner_job_pk=scan_tag.scanner.pk,
            defaults={
                "scan_time": scan_tag.time,
                "raw_scan_tag": prepare_json_object(
                        scan_tag.to_json_object()),

                "raw_metadata": prepare_json_object(result),
                "datasource_last_modified": lm,
                "scanner_job_name": scan_tag.scanner.name,

                "resolution_status": None
            })
    create_aliases(dr)
    return dr


def create_aliases(obj):
    tm = Alias.match_relation.through
    new_objects = []

    metadata = obj.metadata
    if not metadata:
        return

    if (email := metadata.metadata.get("email-account")):
        email_alias = EmailAlias.objects.filter(address__iexact=email)
        add_new_relations(email_alias, new_objects, obj, tm)
    if (adsid := metadata.metadata.get("filesystem-owner-sid")):
        adsid_alias = ADSIDAlias.objects.filter(sid=adsid)
        add_new_relations(adsid_alias, new_objects, obj, tm)
    if (web_domain := metadata.metadata.get("web-domain")):
        web_domain_alias = WebDomainAlias.objects.filter(domain=web_domain)
        add_new_relations(web_domain_alias, new_objects, obj, tm)

    try:
        tm.objects.bulk_create(new_objects, ignore_conflicts=True)
    except Exception:
        logger.error("Failed to create match_relation", exc_info=True)


def add_new_relations(adsid_alias, new_objects, obj, tm):
    for alias in adsid_alias:
        new_objects.append(
            tm(documentreport_id=obj.pk, alias_id=alias.pk))


def handle_match_message(path, scan_tag, result):  # noqa: CCR001, E501 too high cognitive complexity
    locked_qs = DocumentReport.objects.select_for_update(of=('self',))
    new_matches = messages.MatchesMessage.from_json_object(result)
    # The queryset is evaluated and locked here.
    previous_report = (locked_qs.filter(
            path=path, scanner_job_pk=scan_tag.scanner.pk).
            exclude(scan_time=scan_tag.time).order_by("-scan_time").first())

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
                DocumentReport.objects.filter(pk=previous_report.pk).update(
                        scan_time=scan_tag.time)
            else:
                # The file has been edited and the matches are no longer
                # present
                logger.debug("Resource changed: no matches, status is EDITED",
                             report=previous_report)
                DocumentReport.objects.filter(pk=previous_report.pk).update(
                        resolution_status=(
                                DocumentReport.ResolutionChoices.
                                EDITED.value))
        else:
            # The file has been edited, but matches are still present.
            # Resolve the previous ones
            logger.debug("matches still present, status is EDITED",
                         report=previous_report)
            DocumentReport.objects.filter(pk=previous_report.pk).update(
                    resolution_status=(
                            DocumentReport.ResolutionChoices.EDITED.value))

    if new_matches.matched:
        # Collect and store the top-level type label from the matched object
        source = new_matches.handle.source
        while source.handle:
            source = source.handle.source

        dr, _ = DocumentReport.objects.update_or_create(
                path=path, scanner_job_pk=scan_tag.scanner.pk,
                defaults={
                    "scan_time": scan_tag.time,
                    "raw_scan_tag": prepare_json_object(
                            scan_tag.to_json_object()),

                    "source_type": source.type_label,
                    "name": prepare_json_object(
                            new_matches.handle.presentation_name),
                    "sort_key": prepare_json_object(
                            new_matches.handle.sort_key),
                    "sensitivity": new_matches.sensitivity.value,
                    "probability": new_matches.probability,
                    "raw_matches": prepare_json_object(
                            sort_matches_by_probability(result)),
                    "scanner_job_name": scan_tag.scanner.name,

                    "resolution_status": None
                })

        logger.debug("matches, saved DocReport", report=dr)
        return dr
    else:
        logger.debug("No new matches.")
        return None


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


def handle_problem_message(path, scan_tag, result):
    locked_qs = DocumentReport.objects.select_for_update(of=('self',))
    problem = messages.ProblemMessage.from_json_object(result)
    # Queryset is evaluated and locked here.
    previous_report = (locked_qs.filter(
            path=path, scanner_job_pk=scan_tag.scanner.pk).
            exclude(scan_time=scan_tag.time).order_by("-scan_time").first())

    handle = problem.handle if problem.handle else None
    presentation = handle.presentation if handle else "(source)"
    if (previous_report
            and previous_report.resolution_status in [0, None]
            and problem.missing):
        # The file previously had matches, but is now removed.
        logger.debug(
            "Resource deleted, status is REMOVED",
            report=previous_report,
            handle=presentation,
            msgtype="problem",
        )
        DocumentReport.objects.filter(pk=previous_report.pk).update(resolution_status=(
                DocumentReport.ResolutionChoices.REMOVED.value))
        return None
    else:

        # Collect and store the top-level type label from the failing object
        source = problem.handle.source if problem.handle else problem.source
        while source.handle:
            source = source.handle.source

        dr, _ = DocumentReport.objects.update_or_create(
                path=path, scanner_job_pk=scan_tag.scanner.pk,
                defaults={
                    "scan_time": scan_tag.time,
                    "raw_scan_tag": prepare_json_object(
                            scan_tag.to_json_object()),

                    "source_type": source.type_label,
                    "name": prepare_json_object(
                            handle.presentation_name) if handle else "",
                    "sort_key": prepare_json_object(
                            handle.sort_key if handle else "(source)"),
                    "raw_problem": prepare_json_object(result),
                    "scanner_job_name": scan_tag.scanner.name,

                    "resolution_status": None
                })

        logger.debug(
            "Unresolved, saving new report",
            report=dr,
            handle=presentation,
            msgtype="problem",
        )
        return dr


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
                with transaction.atomic():
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
                read=["os2ds_results", "os2ds_events"],
                prefetch_count=8).run_consumer()
