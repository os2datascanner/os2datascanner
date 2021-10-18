"""Runs background jobs."""

import signal

from django.db import transaction
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _

from ...models.background_job import JobState, BackgroundJob

import time
import logging


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
                "-w",
                "--wait",
                default=30,
                metavar="TIME",
                type=int,
                help=_("sleep for %(metavar)s seconds if there were no"
                        " jobs to run"),
        )
        parser.add_argument(
                "-s",
                "--single",
                action='store_true',
                help=_("do not loop: run a single job and then exit"),
        )

    def handle(self, *, wait, single, **kwargs):  # noqa: CCR001, too high cognitive complexity
        running = True

        def _handler(signum, frame):
            nonlocal running
            running = False
        signal.signal(signal.SIGTERM, _handler)

        count = 0
        errors = 0
        try:
            while running:
                job = None

                # Several instances of run_background_jobs can run in parallel,
                # so we need to do a slightly complicated locking dance here to
                # make that safe:
                with transaction.atomic():
                    # QuerySet.select_for_update(skip_locked=True) means that
                    # any objects returned by this query are guaranteed to be
                    # exclusively held by us for the duration of this
                    # transaction, blocking other runners from taking them.
                    # This is a good start, but...
                    job = (
                            BackgroundJob.objects.select_for_update(
                                    skip_locked=True, of=('self',)
                            ).filter(
                                    _exec_state=JobState.WAITING.value
                            ).select_subclasses().first())
                    # ... we can't keep the lock for the entire life of this
                    # job, because we actually use the database to send and
                    # receive status information to and from the outside world,
                    # so we only hold the database-level lock in order to set
                    # our own application-level lock flag
                    if job:
                        job.exec_state = JobState.RUNNING
                        job.save()
                # Now we have a job object that no other runner will try to
                # take, but that clients can still read from and write to

                if job:
                    try:
                        if (job.exec_state == JobState.CANCELLING
                                or job.progress == 1.0):
                            continue
                        try:
                            logger.info(f"starting job {job}")
                            job.run()
                            logger.info(f"finished job {job}")
                            count += 1
                        except Exception:
                            job.exec_state = JobState.FAILED
                            job.save()
                            logger.exception("ignoring unexpected error")
                            errors += 1
                    except KeyboardInterrupt:
                        job.exec_state = JobState.CANCELLING
                    finally:
                        if job.exec_state == JobState.CANCELLING:
                            job.exec_state = JobState.CANCELLED
                            job.save()
                        elif job.exec_state not in (
                                JobState.FAILED,
                                JobState.CANCELLED):
                            job.exec_state = JobState.FINISHED
                            job.save()
                elif not single:
                    # We have no job to do and we're running in a loop. Sleep
                    # to avoid a busy-wait
                    time.sleep(wait)

                if single:
                    running = False
        finally:
            print(_("{0} job(s) completed.").format(count))
            print(_("{0} job(s) failed.").format(errors))
