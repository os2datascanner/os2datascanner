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
import structlog

from os2datascanner.engine2.rules.last_modified import LastModifiedRule
from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.pipeline.utilities.pika import PikaPipelineThread
from ...models.scannerjobs.scanner_model import (Scanner, ScanStatus,
        ScheduledCheckup)

logger = structlog.get_logger(__name__)


def status_message_received_raw(body):
    message = messages.StatusMessage.from_json_object(body)

    status = ScanStatus.objects.filter(scan_tag=body["scan_tag"]).first()
    if not status:
        return

    status.message = message.message
    status.status_is_error = message.status_is_error
    if message.total_objects is not None:
        # ScanStatus uses this value as a divisor, so avoid setting it to zero
        if message.total_objects > 0:
            status.total_objects = (
                    (status.total_objects or 0) + message.total_objects)
        status.explored_sources = (status.explored_sources or 0) + 1
    elif message.object_size is not None and message.object_type is not None:
        status.scanned_size = (status.scanned_size or 0) + message.object_size
        status.scanned_objects = (status.scanned_objects or 0) + 1

    status.save()

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
    scanner = Scanner.objects.get(pk=scan_tag.scanner.pk)
    scan_time = scan_tag.time

    try:
        checkup = ScheduledCheckup.objects.get(
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
                logger.debug("Problem, transient, doing nothing", handle=handle.presentation)
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

    yield from []


class CollectorRunner(PikaPipelineThread):
    def handle_message(self, routing_key, body):
        if routing_key == "os2ds_status":
            return status_message_received_raw(body)
        elif routing_key == "os2ds_checkups":
            return checkup_message_received_raw(body)


class Command(BaseCommand):
    """Command for starting a pipeline collector process."""
    help = __doc__

    def handle(self, *args, **options):
        CollectorRunner(
                exclusive=True,
                read=["os2ds_status", "os2ds_checkups"],
                prefetch_count=8).run_consumer()
