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
import logging
import structlog

from os2datascanner.engine2.rules.last_modified import LastModifiedRule
from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.pipeline.run_stage import _loglevels
from os2datascanner.engine2.pipeline.utilities.pika import PikaPipelineThread

from prometheus_client import Summary, start_http_server

from ...models.scannerjobs.scanner_model import (
    Scanner, ScanStatus, ScheduledCheckup)

logger = structlog.get_logger(__name__)
SUMMARY = Summary("os2datascanner_pipeline_collector_admin",
                  "Messages through admin collector")


def status_message_received_raw(body):
    """A status message for a scannerjob is created in Scanner.run().
    Therefore this method can focus merely on updating the ScanStatus object."""
    message = messages.StatusMessage.from_json_object(body)
    scan_status = ScanStatus.objects.filter(scan_tag=body["scan_tag"])
    if message.total_objects is not None:
        if message.total_objects > 0:
            scan_status.update(
                message=message.message,
                status_is_error=message.status_is_error,
                total_objects=F('total_objects') + message.total_objects,
                explored_sources=F('explored_sources') + 1)
        else:
            scan_status.update(
                message=message.message,
                status_is_error=message.status_is_error)
    elif message.object_size is not None and message.object_type is not None:
        scan_status.update(
            message=message.message,
            status_is_error=message.status_is_error,
            scanned_size=F('scanned_size') + message.object_size,
            scanned_objects=F('scanned_objects') + 1)

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
    except Scanner.DoesNotExist:
        # This is a residual message for a scanner that the administrator has
        # deleted. Throw it away
        return

    scan_time = scan_tag.time

    update_scheduled_checkup(handle, matches, problem, scan_time, scanner)

    yield from []


def update_scheduled_checkup(handle, matches, problem, scan_time, scanner):  # noqa: CCR001, E501 too high cognitive complexity
    try:
        with transaction.atomic():
            checkup = ScheduledCheckup.objects.select_for_update().get(
                handle_representation=handle.to_json_object(),
                scanner=scanner)

            # If we get here, then there was already a checkup object in the
            # database. Let's take a look at it

            if matches:
                if not matches.matched:
                    if (len(matches.matches) == 1
                            and isinstance(matches.matches[0].rule,
                                           LastModifiedRule)):
                        # This object hasn't changed since the last scan. Update
                        # the checkup timestamp so we remember to check it again
                        # next time
                        logger.debug(
                            "LM/no change, updating timestamp",
                            handle=handle.presentation,
                        )
                        checkup.interested_before = scan_time
                        checkup.save()
                    else:
                        # This object has been changed and no longer has any
                        # matches. Hooray! Forget about it
                        logger.debug(
                            "Changed, no matches, deleting",
                            handle=handle.presentation,
                        )
                        checkup.delete()
                else:
                    # This object has changed, but still has matches. Update the
                    # checkup timestamp
                    logger.debug(
                        "Changed, new matches, updating timestamp",
                        handle=handle.presentation,
                    )
                    checkup.interested_before = scan_time
                    checkup.save()
            elif problem:
                if problem.missing:
                    # Permanent error, so this object has been deleted. Forget
                    # about it
                    logger.debug("Problem, deleted, deleting", handle=handle.presentation)
                    checkup.delete()
                else:
                    # Transient error -- do nothing. In particular, don't update
                    # the checkup timestamp; we don't want to forget about changes
                    # between the last match and this error
                    logger.debug("Problem, transient, doing nothing",
                                 handle=handle.presentation)
    except ScheduledCheckup.DoesNotExist:
        if ((matches and matches.matched)
                or (problem and not problem.missing)):
            logger.debug("Interesting, creating", handle=handle.presentation)
            # An object with a transient problem or with real matches is an
            # object we'll want to check up on again later
            ScheduledCheckup.objects.create(
                handle_representation=handle.to_json_object(),
                scanner=scanner,
                # XXX: ideally we'd detect if a LastModifiedRule is the
                # victim of a transient failure so that we can preserve the
                # date to scan the object properly next time, but we don't
                # (yet) get enough information out of the pipeline for that
                interested_before=scan_time)
        else:
            logger.debug("Not interesting, doing nothing", handle=handle.presentation)
    except DataError as de:
        # DataError occurs when something went wrong trying to select or
        # create/update data in the database. Often regarding ScheduledCheckups
        # it is related to the json data. For now, we only log the error message.
        logger.error("Could not get or create object, due to DataError",
                     error=de)


class CollectorRunner(PikaPipelineThread):
    start_http_server(9091)

    def handle_message(self, routing_key, body):
        with SUMMARY.time():
            logger.debug(
                    "raw message received",
                    routing_key=routing_key,
                    body=body)
            with transaction.atomic():
                if routing_key == "os2ds_status":
                    yield from status_message_received_raw(body)
                elif routing_key == "os2ds_checkups":
                    yield from checkup_message_received_raw(body)


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
                read=["os2ds_status", "os2ds_checkups"],
                prefetch_count=8).run_consumer()
