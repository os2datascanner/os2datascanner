"""Runs background jobs."""

from os import getenv
import sys
import signal
from typing import Optional

from django.db import transaction
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from prometheus_client import CollectorRegistry, Enum, push_to_gateway
from django.conf import settings

from ...models.background_job import JobState, BackgroundJob
from os2datascanner.utils import debug
from os2datascanner.utils.log_levels import log_levels

import time
import logging


logger = logging.getLogger(
        "os2datascanner.projects.admin.core.management"
        ".commands.run_background_jobs")
# Registry for Prometheus
REGISTRY = CollectorRegistry()
JOB_STATE = Enum('background_job_status',
                 'Shows the current/last state of given background job',
                 states=['waiting', 'running', 'cancelling',
                         'finished', 'cancelled', 'failed'],
                 labelnames=['JobLabel', 'OrgSlug', 'OrgId'])
REGISTRY.register(JOB_STATE)  # Register the metric
PUSHGATEWAY_HOST = settings.PUSHGATEWAY_HOST


def acquire_job(**filters) -> Optional[BackgroundJob]:
    """Claims responsibility for a BackgroundJob from the database, if there is
    one that hasn't already been claimed by another runner process."""
    # Several instances of run_background_jobs can run in parallel, so we need
    # to do a slightly complicated locking dance here to make that safe:
    with transaction.atomic():
        # QuerySet.select_for_update(skip_locked=True) means that any objects
        # returned by this query are guaranteed to be exclusively held by us
        # for the duration of this transaction, blocking other runners from
        # taking them. This is a good start, but...
        job = (
                BackgroundJob.objects.select_for_update(
                        skip_locked=True, of=('self',)
                ).filter(
                        _exec_state=JobState.WAITING.value,
                        **filters
                ).select_subclasses().first())
        # ... we can't keep the lock for the entire life of this job, because
        # we actually use the database to send and receive status information
        # to and from the outside world, so we only hold the database-level
        # lock in order to set our own application-level lock flag

        if job:
            job.exec_state = JobState.RUNNING
            job.save()

            # Now we have a job object that no other runner will try to take,
            # but that clients can still read from and write to
            return job
        else:
            return None


def _get_org(j: BackgroundJob):
    """Attempts to extract an admin.organizations Organization from the given
    BackgroundJob."""
    # This method is a hack: the BackgroundJob API doesn't expose an
    # organisation, so run_background_jobs shouldn't actually care about it.
    # We need it for Prometheus metrics, though...
    if hasattr(j, "organization"):  # MSGraphImportJob
        return j.organization
    elif (hasattr(j, "realm")
            and hasattr(j.realm, "organization")):  # ImportJob (LDAP)
        return j.realm.organization
    else:
        return None


def publish_job_state(job: BackgroundJob):
    org = _get_org(job)
    org_slug = org.slug if org else "unknown"
    org_id = org.pk if org else "N/A"

    JOB_STATE.labels(
            JobLabel=job.job_label,
            OrgSlug=org_slug,
            OrgId=org_id).state(job.exec_state.value)
    push_to_gateway(
            gateway=PUSHGATEWAY_HOST,
            job='pushgateway', registry=REGISTRY)


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
        parser.add_argument(
                "--log",
                default=None,
                help="change the level at which log messages will be printed",
                choices=log_levels.keys()
        )

    def handle(self, *, wait, single, log, **kwargs):  # noqa: CCR001, C901
        # leave all loggers from external libraries at default(WARNING) level.
        # change formatting to include datestamp
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(format=fmt, datefmt='%Y-%m-%d %H:%M:%S')

        # set level for root logger
        if log is None:
            log = getenv("LOG_LEVEL", "info")
        root_logger = logging.getLogger("os2datascanner")
        root_logger.setLevel(log_levels[log])

        running = True

        def _handler(signum, frame):
            nonlocal running
            running = False

            raise BackgroundJob.MustStop()

        signal.signal(signal.SIGTERM, _handler)
        debug.register_debug_signal()

        count = 0
        errors = 0
        try:
            job = None

            def _print_job_information(signum, frame):
                job_info = None
                if job:
                    job_info = (
                            BackgroundJob.objects.select_subclasses()
                            .filter(pk=job.pk).values().first())
                print("Current job:", file=sys.stderr)
                print(f"\t{job_info}")

            with debug.debug_helper(_print_job_information):
                while running:
                    job = acquire_job()

                    if job:
                        publish_job_state(job)
                        try:
                            if (job.exec_state == JobState.CANCELLING
                                    or job.progress == 1.0):
                                continue
                            try:
                                logger.info(f"starting job {job}")
                                job.run()
                                logger.info(f"finished job {job}")
                                count += 1
                            except BackgroundJob.MustStop:
                                job.exec_state = JobState.FAILED
                                job.status = "Interrupted by environment"
                                job.save()
                                publish_job_state(job)
                                errors += 1
                            except Exception:
                                job.exec_state = JobState.FAILED
                                job.save()
                                publish_job_state(job)
                                logger.exception("ignoring unexpected error")
                                errors += 1
                        except KeyboardInterrupt:
                            job.exec_state = JobState.CANCELLING
                            publish_job_state(job)
                        finally:
                            if job.exec_state == JobState.CANCELLING:
                                job.exec_state = JobState.CANCELLED
                                job.save()
                            elif job.exec_state not in (
                                    JobState.FAILED,
                                    JobState.CANCELLED):
                                job.exec_state = JobState.FINISHED
                                job.save()
                            publish_job_state(job)
                            job.finish()
                            job = None
                    elif not single:
                        # We have no job to do and we're running in a loop.
                        # Sleep to avoid a busy-wait
                        time.sleep(wait)

                    if single:
                        running = False
        finally:
            print(_("{0} job(s) completed.").format(count))
            print(_("{0} job(s) failed.").format(errors))
