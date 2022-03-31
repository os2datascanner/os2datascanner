"""Runs background jobs."""

import sys
import signal
from typing import Optional
import traceback

from django.db import transaction
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from prometheus_client import CollectorRegistry, Enum, push_to_gateway
from django.conf import settings

from ...models.background_job import JobState, BackgroundJob
from os2datascanner.engine2.pipeline.run_stage import _loglevels

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


def backtrace(signal, frame):
    print("Got SIGUSR1, printing stacktrace:", file=sys.stderr)
    traceback.print_stack()


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
                default="info",
                help="change the level at which log messages will be printed",
                choices=_loglevels.keys()
        )

    def handle(self, *, wait, single, log, **kwargs):  # noqa: CCR001
        # leave all loggers from external libraries at default(WARNING) level.
        # change formatting to include datestamp
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(format=fmt, datefmt='%Y-%m-%d %H:%M:%S')
        # set level for root logger
        root_logger = logging.getLogger("os2datascanner")
        root_logger.setLevel(_loglevels[log])

        running = True

        def _handler(signum, frame):
            nonlocal running
            running = False

        signal.signal(signal.SIGTERM, _handler)
        signal.signal(signal.SIGUSR1, backtrace)

        count = 0
        errors = 0
        try:
            while running:
                job = acquire_job()

                if job:
                    job_label = job.job_label
                    # TODO: This way of getting org info will only work for import jobs.
                    org_slug = job.realm.organization.slug or 'No Org Info'
                    org_id = job.realm.organization.pk or 'No Org Info'

                    JOB_STATE.labels(
                            JobLabel=job_label,
                            OrgSlug=org_slug,
                            OrgId=org_id).state('running')
                    push_to_gateway(
                            gateway=PUSHGATEWAY_HOST,
                            job='pushgateway', registry=REGISTRY)

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
                            JOB_STATE.labels(
                                    JobLabel=job_label, OrgSlug=org_slug,
                                    OrgId=org_id).state('failed')
                            push_to_gateway(
                                    gateway=PUSHGATEWAY_HOST,
                                    job='pushgateway', registry=REGISTRY)
                            logger.exception("ignoring unexpected error")
                            errors += 1
                    except KeyboardInterrupt:
                        job.exec_state = JobState.CANCELLING
                        JOB_STATE.labels(
                                JobLabel=job_label, OrgSlug=org_slug,
                                OrgId=org_id).state('cancelling')
                        push_to_gateway(
                                gateway=PUSHGATEWAY_HOST,
                                job='pushgateway', registry=REGISTRY)
                    finally:
                        if job.exec_state == JobState.CANCELLING:
                            job.exec_state = JobState.CANCELLED
                            job.save()
                            JOB_STATE.labels(
                                    JobLabel=job_label, OrgSlug=org_slug,
                                    OrgId=org_id).state('cancelled')
                            push_to_gateway(
                                    gateway=PUSHGATEWAY_HOST,
                                    job='pushgateway', registry=REGISTRY)
                        elif job.exec_state not in (
                                JobState.FAILED,
                                JobState.CANCELLED):
                            job.exec_state = JobState.FINISHED
                            job.save()
                            JOB_STATE.labels(
                                    JobLabel=job_label, OrgSlug=org_slug,
                                    OrgId=org_id).state('finished')
                            push_to_gateway(
                                    gateway=PUSHGATEWAY_HOST,
                                    job='pushgateway', registry=REGISTRY)
                elif not single:
                    # We have no job to do and we're running in a loop. Sleep
                    # to avoid a busy-wait
                    time.sleep(wait)

                if single:
                    running = False
        finally:
            print(_("{0} job(s) completed.").format(count))
            print(_("{0} job(s) failed.").format(errors))
