from abc import abstractmethod
from time import sleep
import uuid
from typing import Optional

from django.db import models, transaction
from model_utils.managers import InheritanceManager
from django.utils.translation import gettext_lazy as _

from .utilities import ModelChoiceEnum


class JobState(ModelChoiceEnum):
    WAITING = ("waiting", _("waiting"))
    # This job is awaiting execution.

    RUNNING = ("running", _("running"))
    # This job is running on a specific executor.
    CANCELLING = ("cancelling", _("cancelling"))
    # This job is running on a specific executor, but has been asked to
    # stop.

    FINISHED = ("finished", _("finished"))
    # Execution of this job was successful.
    CANCELLED = ("cancelled", _("cancelled"))
    # Execution of this job was cancelled by the user.
    FAILED = ("failed", _("failed"))
    # Execution of this job failed.


class BackgroundJob(models.Model):
    """A BackgroundJob represents a long-running background task. It provides
    communication and status updates on the task's execution; its subclasses
    implement specific tasks."""

    class MustStop(BaseException):
        """If the execution environment for a BackgroundJob is informed that
        its execution must soon stop, a BackgroundJob.MustStop exception will
        be raised. Handlers for this exception should complete quickly, as the
        execution environment is likely to be forcibly terminated within a few
        seconds.

        There are no values associated with MustStop exceptions."""

    objects = InheritanceManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(
            verbose_name=_("job creation time"),
            auto_now_add=True)
    changed_at = models.DateTimeField(
            verbose_name=_("job update time"),
            auto_now=True)

    _exec_state = models.CharField(
            max_length=30,
            verbose_name=_("execution state"),
            choices=JobState.choices(),
            null=False, blank=False, default=JobState.WAITING.value)
    status = models.TextField(
            verbose_name=_("last status message"),
            blank=True)

    @property
    def exec_state(self):
        return JobState(self._exec_state)

    @exec_state.setter
    def exec_state(self, state: JobState):
        self._exec_state = state.value

    @transaction.atomic
    def cancel(self) -> bool:
        """Requests that this job be terminated. (If execution has not yet
        started, then the object will be deleted; otherwise, it will continue
        to exist to provide status updates from the job runner.)"""
        if self.exec_state == JobState.WAITING:
            self.delete()
            return True
        elif self.exec_state == JobState.RUNNING:
            self.update(_exec_state=JobState.CANCELLING.value)
        return self.cancel_requested and self.exec_state == JobState.CANCELLED

    @property
    def progress(self) -> Optional[float]:
        """If this job is underway, returns a value between 0.0 and 1.0
        corresponding to how complete it is. If this job is not yet underway,
        or has been cancelled, returns None."""
        return None

    @property
    @abstractmethod
    def job_label(self) -> str:
        """ Should return a str simply stating what type of job it is.
        For example, an ImportJob could return just that: Import Job.
        Mainly used as a way to label metrics for prometheus/grafana.
        """

    def run(self):
        """Runs this job to completion (or cancellation), updating its
        properties until it finishes."""
        raise TypeError(
                "BackgroundJob.run does nothing --"
                " call this method on a subclass")

    class Meta:
        ordering = ['-changed_at']


class CounterJob(BackgroundJob):
    """A CounterJob is an example of how to use BackgroundJob. Its very
    exciting background task is to increment a counter by one every second."""
    count_to = models.IntegerField()
    counted_to = models.IntegerField(blank=True, null=True, default=0)

    @property
    def progress(self):
        return (self.counted_to / self.count_to
                if self.counted_to is not None
                else None)

    @property
    def job_label(self) -> str:
        return "Counter Job"

    def run(self):
        self.refresh_from_db()
        count = 0
        while count is not None and count < self.count_to:
            with transaction.atomic():
                if self.exec_state != JobState.RUNNING:
                    self.status = "Interrupted after {0}".format(count)
                    count = None
                else:
                    count += 1
                    self.status = "Counted to {0}".format(count)
                    self.counted_to = count
                self.save()
            print(self.status)
            sleep(1.0)
            self.refresh_from_db()
