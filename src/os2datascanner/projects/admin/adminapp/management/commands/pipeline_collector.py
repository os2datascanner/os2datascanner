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

from django.db.models import F
from django.db import transaction
from django.db.utils import DataError
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
import logging
import structlog
import math

from os2datascanner.engine2.rules.last_modified import LastModifiedRule
from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.pipeline.run_stage import _loglevels
from os2datascanner.engine2.pipeline.utilities.pika import PikaPipelineThread

from prometheus_client import Summary, start_http_server

from ...models.scannerjobs.scanner import (
    Scanner, ScanStatus, ScheduledCheckup, ScanStatusSnapshot)
from ...models.usererrorlog import UserErrorLog
from ...notification import send_mail_upon_completion

logger = structlog.get_logger(__name__)
SUMMARY = Summary("os2datascanner_pipeline_collector_admin",
                  "Messages through admin collector")


def status_message_received_raw(body):
    """A status message for a scannerjob is created in Scanner.run().
    Therefore this method can focus merely on updating the ScanStatus object."""
    message = messages.StatusMessage.from_json_object(body)

    try:
        scanner = Scanner.objects.get(pk=message.scan_tag.scanner.pk)
    except Scanner.DoesNotExist:
        # This is a residual message for a scanner that the administrator has
        # deleted. Throw it away
        return

    locked_qs = ScanStatus.objects.select_for_update(
        of=('self',)
    ).filter(
        scanner=scanner,
        scan_tag=body["scan_tag"]
    )
    # Queryset is evaluated immediately with .first() to lock the database entry.
    locked_qs.first()

    if message.total_objects is not None:
        # An explorer has finished exploring a Source
        locked_qs.update(
                message=message.message,
                last_modified=timezone.now(),
                status_is_error=message.status_is_error,
                total_objects=F('total_objects') + message.total_objects,
                total_sources=F('total_sources') + (message.new_sources or 0),
                explored_sources=F('explored_sources') + 1)

    elif message.object_size is not None and message.object_type is not None:
        # A worker has finished processing a Handle
        locked_qs.update(
                message=message.message,
                last_modified=timezone.now(),
                status_is_error=message.status_is_error,
                scanned_size=F('scanned_size') + message.object_size,
                scanned_objects=F('scanned_objects') + 1)

    # Get the frequency setting and decide whether or not to create a snapshot
    snapshot_param = settings.SNAPSHOT_PARAMETER
    scan_status = locked_qs.first()
    if scan_status:
        n_total = scan_status.total_objects
        if n_total and n_total > 0:
            # Calculate a frequency for how often to take a snapshot.
            # n_total must be a least 2 for this to work.
            frequency = n_total * math.log(snapshot_param, max(n_total, 2))
            # Decide whether it is time to take a snapshot.
            take_snap = scan_status.scanned_objects % max(1, math.floor(frequency))
            if take_snap == 0:
                ScanStatusSnapshot.objects.create(
                    scan_status=scan_status,
                    time_stamp=timezone.now(),
                    total_sources=scan_status.total_sources,
                    explored_sources=scan_status.explored_sources,
                    total_objects=scan_status.total_objects,
                    scanned_objects=scan_status.scanned_objects,
                    scanned_size=scan_status.scanned_size,
                )

        if scan_status.finished:
            # Update last_modified for scanner
            scanner.e2_last_run_at = scan_status.last_modified
            scanner.save()
            # Send email upon scannerjob completion
            logger.info("Sending notification mail for finished scannerjob.")
            send_mail_upon_completion(scanner, scan_status)

    yield from []


def problem_message_recieved_raw(body):
    """Send the error message on to the UserErrorLog object."""
    message = messages.ProblemMessage.from_json_object(body)

    try:
        scanner = Scanner.objects.get(pk=message.scan_tag.scanner.pk)
    except Scanner.DoesNotExist:
        # This is a residual message for a scanner that the administrator has
        # deleted. Throw it away
        return

    error_message = message.message
    # Different types of scans have different source classes, where the
    # source path is contained differently.
    if message.handle and message.handle.presentation_url:
        path = message.handle.presentation_url
    elif message.handle and message.handle.presentation:
        path = message.handle.presentation
    elif message.handle and message.handle.presentation_name:
        path = message.handle.presentation_name
    else:
        path = ""

    # Determine related ScanStatus object
    scan_status = ScanStatus.objects.filter(  # Uses the "ss_pc_lookup" index
            scanner=scanner,
            scan_tag=body["scan_tag"]).first()

    if scan_status:
        logger.info(
            f"Logging the error: '{error_message}' from scanner {scan_status.scanner.name}.")
        UserErrorLog.objects.create(
            scan_status=scan_status,
            error_message=error_message,
            path=path,
            organization=scanner.organization,
            is_new=True
        )

    yield from []


def checkup_message_received_raw(body):
    handle = None
    scan_tag = None
    matches = None
    problem = None
    if "message" in body:  # Problem message
        problem = messages.ProblemMessage.from_json_object(body)
        handle = problem.handle
        scan_tag = problem.scan_tag
    elif "matches" in body:  # Matches message
        matches = messages.MatchesMessage.from_json_object(body)
        handle = matches.handle
        scan_tag = matches.scan_spec.scan_tag

    if not scan_tag or not handle:
        return
    try:
        scanner = Scanner.objects.get(pk=scan_tag.scanner.pk)
        ScanStatus.objects.get(scan_tag=scan_tag.to_json_object())
    except Scanner.DoesNotExist:
        # This is a residual message for a scanner that the administrator has
        # deleted. Throw it away
        return
    except ScanStatus.DoesNotExist:
        # This means that there is no corresponding ScanStatus object.
        # Likely, this means that the scan has been cancelled. Tell processes to throwaway messages.
        msg = messages.CommandMessage(
            abort=messages.ScanTagFragment.from_json_object(
                scan_tag.to_json_object()))
        with PikaPipelineThread() as p:
            p.enqueue_message(
                "", msg.to_json_object(),
                "broadcast", priority=10)
            p.enqueue_stop()
            p.run()
        return

    scan_time = scan_tag.time

    update_scheduled_checkup(
            handle.censor(), matches, problem, scan_time, scanner)

    yield from []


def update_scheduled_checkup(handle, matches, problem, scan_time, scanner):  # noqa: CCR001, E501 too high cognitive complexity
    locked_qs = ScheduledCheckup.objects.select_for_update(
        of=('self',)
    ).filter(
        scanner=scanner,
        handle_representation=handle.to_json_object()
    )
    # Queryset is evaluated immediately with .first() to lock the database entry.
    locked_qs.first()
    if locked_qs:
        # There was already a checkup object in the database. Let's take a
        # look at it
        if matches:
            if not matches.matched:
                if (len(matches.matches) == 1
                        and isinstance(matches.matches[0].rule,
                                       LastModifiedRule)):
                    # This object hasn't changed since the last scan.
                    # Update the checkup timestamp so we remember to check
                    # it again next time
                    logger.debug(
                            "LM/no change, updating timestamp",
                            handle=handle.presentation)
                    locked_qs.update(
                            interested_before=scan_time)
                else:
                    # This object has been changed and no longer has any
                    # matches. Hooray! Forget about it
                    logger.debug(
                            "Changed, no matches, deleting",
                            handle=handle.presentation)
                    locked_qs.delete()
            else:
                # This object has changed, but still has matches. Update
                # the checkup timestamp
                logger.debug(
                        "Changed, new matches, updating timestamp",
                        handle=handle.presentation)
                locked_qs.update(
                        interested_before=scan_time)
        elif problem:
            if problem.missing:
                # Permanent error, so this object has been deleted. Forget
                # about it
                logger.debug(
                        "Problem, deleted, deleting",
                        handle=handle.presentation)
                locked_qs.delete()
            else:
                # Transient error -- do nothing. In particular, don't
                # update the checkup timestamp; we don't want to forget
                # about changes between the last match and this error
                logger.debug("Problem, transient, doing nothing",
                             handle=handle.presentation)

    elif ((matches and matches.matched)
            or (problem and not problem.missing)):
        logger.debug(
                "Interesting, creating", handle=handle.presentation)
        # An object with a transient problem or with real matches is an
        # object we'll want to check up on again later
        ScheduledCheckup.objects.update_or_create(
                handle_representation=handle.to_json_object(),
                scanner=scanner,
                # XXX: ideally we'd detect if a LastModifiedRule is the
                # victim of a transient failure so that we can preserve
                # the date to scan the object properly next time, but
                # we don't (yet) get enough information out of the
                # pipeline for that
                defaults={
                    "interested_before": scan_time
                })
    else:
        logger.debug(
                "Not interesting, doing nothing",
                handle=handle.presentation)


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
            try:
                with transaction.atomic():
                    if routing_key == "os2ds_status":
                        yield from status_message_received_raw(body)
                    elif routing_key == "os2ds_checkups":
                        yield from checkup_message_received_raw(body)
                    elif routing_key == "os2ds_problems":
                        yield from problem_message_recieved_raw(body)
            except DataError as de:
                # DataError occurs when something went wrong trying to select
                # or create/update data in the database. Often regarding
                # ScheduledCheckups it is related to the json data. For now, we
                # only log the error message.
                logger.error(
                        "Could not get or create object, due to DataError",
                        error=de)


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
                read=["os2ds_status", "os2ds_checkups", "os2ds_problems"],
                prefetch_count=8).run_consumer()
