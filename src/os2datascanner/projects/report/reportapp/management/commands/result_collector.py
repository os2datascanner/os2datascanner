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

import logging
import structlog
from django.db import transaction
from django.core.management.base import BaseCommand

from os2datascanner.utils import debug
from os2datascanner.utils.log_levels import log_levels
from os2datascanner.engine2.conversions.types import OutputType
from os2datascanner.engine2.model.core import Handle, Source
from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.pipeline.utilities.pika import PikaPipelineThread
from os2datascanner.engine2.rules.last_modified import LastModifiedRule

from os2datascanner.projects.report.organizations.models import Alias, Organization

from os2datascanner.utils.system_utilities import time_now
from prometheus_client import Summary, start_http_server

from ...models.documentreport import DocumentReport
from ...utils import prepare_json_object


logger = structlog.get_logger(__name__)
SUMMARY = Summary("os2datascanner_result_collector_report",
                  "Messages through result collector report")

ResolutionChoices = DocumentReport.ResolutionChoices


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

    with transaction.atomic():
        if queue == "matches":
            handle_match_message(tag, body)
        elif queue == "problem":
            handle_problem_message(tag, body)
        elif queue == "metadata":
            handle_metadata_message(tag, body)

    yield from []


def owner_from_metadata(message: messages.MetadataMessage) -> str:
    owner = ""
    if (email := message.metadata.get("email-account")
            or message.metadata.get("msgraph-owner-account")):
        owner = email
    if adsid := message.metadata.get("filesystem-owner-sid"):
        owner = adsid
    if web_domain := message.metadata.get("web-domain"):
        owner = web_domain

    return owner


def handle_metadata_message(scan_tag, result):
    # Evaluate the queryset that is updated later to lock it.
    message = messages.MetadataMessage.from_json_object(result)
    path = message.handle.crunch(hash=True)
    owner = owner_from_metadata(message)

    DocumentReport.objects.select_for_update(
        of=('self',)
    ).filter(
        path=path,
        scanner_job_pk=scan_tag.scanner.pk
    ).first()

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
                "only_notify_superadmin": scan_tag.scanner.test,
                "resolution_status": None,
                "organization": get_org_from_scantag(scan_tag),
                "owner": owner,
            })
    create_aliases(dr)
    return dr


def create_aliases(obj):
    tm = Alias.match_relation.through
    new_objects = []

    metadata = obj.metadata
    if not metadata:
        return

    # TODO: Could use DR's "owner" field too, might be a small benefit.
    if (email := metadata.metadata.get("email-account")
            or metadata.metadata.get("msgraph-owner-account")):
        email_alias = Alias.objects.filter(_alias_type="email", _value__iexact=email)
        add_new_relations(email_alias, new_objects, obj, tm)
    if (adsid := metadata.metadata.get("filesystem-owner-sid")):
        adsid_alias = Alias.objects.filter(_alias_type="SID", _value=adsid)
        add_new_relations(adsid_alias, new_objects, obj, tm)
    if (web_domain := metadata.metadata.get("web-domain")):
        web_domain_alias = Alias.objects.filter(_alias_type="generic", _value=web_domain)
        add_new_relations(web_domain_alias, new_objects, obj, tm)

    try:
        tm.objects.bulk_create(new_objects, ignore_conflicts=True)
    except Exception:
        logger.error("Failed to create match_relation", exc_info=True)


def add_new_relations(adsid_alias, new_objects, obj, tm):
    for alias in adsid_alias:
        new_objects.append(
            tm(documentreport_id=obj.pk, alias_id=alias.pk))


def handle_match_message(scan_tag, result):  # noqa: CCR001, E501 too high cognitive complexity
    locked_qs = DocumentReport.objects.select_for_update(of=('self',))
    new_matches = messages.MatchesMessage.from_json_object(result)
    path = new_matches.handle.crunch(hash=True)
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
                        scan_time=scan_tag.time,
                        # If there is a problem associated with this report, we
                        # no longer care about it
                        raw_problem=None)
            else:
                # The file has been edited and the matches are no longer
                # present
                logger.debug("Resource changed: no matches, status is EDITED",
                             report=previous_report)
                DocumentReport.objects.filter(pk=previous_report.pk).update(
                        resolution_status=ResolutionChoices.EDITED.value,
                        resolution_time=time_now(),
                        raw_problem=None)
        else:
            # The file has been edited, but matches are still present.
            # Resolve the previous ones
            logger.debug("matches still present, status is EDITED",
                         report=previous_report)
            DocumentReport.objects.filter(pk=previous_report.pk).update(
                    resolution_status=ResolutionChoices.EDITED.value,
                    resolution_time=time_now(),
                    raw_problem=None)

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
                    "only_notify_superadmin": scan_tag.scanner.test,
                    "resolution_status": None,
                    "organization": get_org_from_scantag(scan_tag),

                    "raw_problem": None,
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


def handle_problem_message(scan_tag, result):
    locked_qs = DocumentReport.objects.select_for_update(of=('self',))
    problem = messages.ProblemMessage.from_json_object(result)
    obj = (problem.handle if problem.handle else problem.source)
    path = obj.crunch(hash=True)

    # Queryset is evaluated and locked here.
    previous_report = (locked_qs.filter(
            path=path, scanner_job_pk=scan_tag.scanner.pk).
            order_by("-scan_time").first())

    handle = problem.handle if problem.handle else None
    presentation = str(handle) if handle else "(source)"

    match (previous_report, problem):
        case (None, messages.ProblemMessage(missing=True)):
            # We've received a report that a resource is missing, but we have
            # nothing associated with it. Nothing to do
            logger.debug("Problem message of no relevance. Throwing away.")
            pass
        case (DocumentReport() as prev, messages.ProblemMessage(missing=True)) \
                if not prev.resolution_status:
            # A resource for which we have some unresolved reports has been
            # deleted.
            # If resolution status is "OTHER" or None: (I.e. 0 or None)
            # Mark it as removed and remove its raw_problem message.

            logger.debug(
                "Resource deleted, status is REMOVED",
                report=previous_report,
                handle=presentation,
                msgtype="problem",
            )
            DocumentReport.objects.filter(pk=prev.pk).update(
                resolution_status=ResolutionChoices.REMOVED.value,
                resolution_time=time_now(),
                raw_problem=None)
        case (DocumentReport() as prev,
              messages.ProblemMessage(missing=False)) if prev.resolution_status is not None:
            # A known resource, which isn't missing, has a problem, but has already been resolved.
            # Nothing to do, problem is not relevant anymore.
            if prev.scan_time == scan_tag.time:
                logger.warning(
                        "detected duplicated ProblemMessage for scan"
                        f" {scan_tag}: has the system been restarted?")
            else:
                logger.debug(
                        "Resource already resolved."
                        " Problem message of no relevance. ")

        case (DocumentReport() as prev,
              messages.ProblemMessage(missing=True)) if prev.resolution_status:
            # A resource for which we have some reports has been deleted, but
            # it's also been resolved. Nothing to do
            pass
        case (None, messages.ProblemMessage()):
            # A resource not previously known to us has a problem. Store it
            source = (
                    problem.handle.source
                    if problem.handle else problem.source)
            while source.handle:
                source = source.handle.source

            dr = DocumentReport.objects.create(
                    path=path,
                    scanner_job_pk=scan_tag.scanner.pk,

                    scan_time=scan_tag.time,
                    raw_scan_tag=prepare_json_object(
                            scan_tag.to_json_object()),

                    source_type=source.type_label,
                    name=prepare_json_object(
                            handle.presentation_name) if handle else "",
                    sort_key=prepare_json_object(
                            handle.sort_key if handle else "(source)"),
                    raw_problem=prepare_json_object(result),
                    scanner_job_name=scan_tag.scanner.name,
                    only_notify_superadmin=scan_tag.scanner.test,
                    resolution_status=None,
                    organization=get_org_from_scantag(scan_tag))

            logger.debug(
                "Unresolved, created new report",
                report=dr,
                handle=presentation,
                msgtype="problem",
            )
            return dr
        case (DocumentReport() as prev, messages.ProblemMessage()):
            # A resource known to us (either because of its matches or because
            # of a pre-existing problem) has a new problem, but we can't say
            # for sure that it's been deleted. Put the new problem in the
            # existing report
            DocumentReport.objects.filter(pk=prev.pk).update(
                    raw_problem=prepare_json_object(problem.to_json_object()))
            return prev


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


def get_org_from_scantag(scan_tag):
    return Organization.objects.filter(uuid=scan_tag.organisation.uuid).first()


class ResultCollectorRunner(PikaPipelineThread):
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


class Command(BaseCommand):
    """Command for starting a result collector process."""
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
                "--log",
                default="info",
                help="change the level at which log messages will be printed",
                choices=log_levels.keys())

    def handle(self, *args, log, **options):
        debug.register_debug_signal()

        # change formatting to include datestamp
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(format=fmt, datefmt='%Y-%m-%d %H:%M:%S')
        # set level for root logger
        logging.getLogger("os2datascanner").setLevel(log_levels[log])

        ResultCollectorRunner(
            read=["os2ds_results"],
            prefetch_count=8).run_consumer()
