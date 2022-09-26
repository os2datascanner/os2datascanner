# -*- coding: utf-8 -*-
# encoding: utf-8
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
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )

"""Contains Django model for the scanner types."""

import datetime
from enum import Enum
import os
from typing import Iterator
import structlog

from django.db import models
from django.conf import settings
from django.core.validators import validate_comma_separated_integer_list
from django.db.models import JSONField
from django.db.models.signals import post_delete
from django.utils.translation import ugettext_lazy as _
from django.dispatch import receiver
from django.utils import timezone

from model_utils.managers import InheritanceManager
from recurrence.fields import RecurrenceField

from os2datascanner.utils.system_utilities import time_now
from os2datascanner.engine2.model.core import Handle, Source
from os2datascanner.engine2.rules.meta import HasConversionRule
from os2datascanner.engine2.rules.logical import OrRule, AndRule, AllRule, make_if
from os2datascanner.engine2.rules.dimensions import DimensionsRule
from os2datascanner.engine2.rules.last_modified import LastModifiedRule
import os2datascanner.engine2.pipeline.messages as messages
from os2datascanner.engine2.pipeline.utilities.pika import PikaPipelineThread
from os2datascanner.engine2.conversions.types import OutputType
from mptt.models import TreeManyToManyField

from ..authentication import Authentication
from ..rules.rule import Rule

logger = structlog.get_logger(__name__)
base_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


class Scanner(models.Model):

    """A scanner, i.e. a template for actual scanning jobs."""
    objects = InheritanceManager()

    linkable = False

    name = models.CharField(
        max_length=256,
        unique=True,
        null=False,
        db_index=True,
        verbose_name='Navn'
    )

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='scannerjob',
        verbose_name=_('organization'),
        default=None,
        null=True,
    )

    org_unit = TreeManyToManyField(
        "organizations.OrganizationalUnit",
        related_name="scanners",
        blank=True,
        verbose_name=_("organizational unit"),
    )

    schedule = RecurrenceField(
        max_length=1024,
        null=True,
        blank=True,
        verbose_name='Planlagt afvikling'
    )

    do_ocr = models.BooleanField(
        default=False,
        verbose_name='Scan billeder'
    )

    do_last_modified_check = models.BooleanField(
        default=True,
        verbose_name='Tjek dato for sidste ændring',
    )

    only_notify_superadmin = models.BooleanField(
        default=False,
        verbose_name='Underret kun superadmin',
    )

    columns = models.CharField(validators=[validate_comma_separated_integer_list],
                               max_length=128,
                               null=True,
                               blank=True
                               )

    rules = models.ManyToManyField(Rule,
                                   blank=True,
                                   verbose_name='Regler',
                                   related_name='scanners')

    VALID = 1
    INVALID = 0

    validation_choices = (
        (INVALID, "Ugyldig"),
        (VALID, "Gyldig"),
    )

    url = models.CharField(max_length=2048, blank=False, verbose_name='URL')

    authentication = models.OneToOneField(Authentication,
                                          null=True,
                                          related_name='%(app_label)s_%(class)s_authentication',
                                          verbose_name='Brugernavn',
                                          on_delete=models.SET_NULL)

    validation_status = models.IntegerField(choices=validation_choices,
                                            default=INVALID,
                                            verbose_name='Valideringsstatus')

    exclusion_rules = models.ManyToManyField(Rule,
                                             blank=True,
                                             verbose_name='Udelukkelsesregler',
                                             related_name='scanners_ex_rules')

    e2_last_run_at = models.DateTimeField(null=True)

    def verify(self) -> bool:
        """Method documentation"""
        raise NotImplementedError("Scanner.verify")

    @property
    def schedule_description(self):
        """A lambda for creating schedule description strings."""
        if any(self.schedule.occurrences()):
            return u"Ja"
        else:
            return u"Nej"

    # Run error messages
    HAS_NO_RULES = (
        "Scannerjobbet kunne ikke startes," +
        " fordi det ingen tilknyttede regler har."
    )
    NOT_VALIDATED = (
        "Scannerjobbet kunne ikke startes," +
        " fordi det ikke er blevet valideret."
    )
    ALREADY_RUNNING = (
        "Scannerjobbet kunne ikke startes," +
        " da dette scan er igang."
    )

    # First possible start time
    FIRST_START_TIME = datetime.time(hour=18, minute=0)
    # Amount of quarter-hours that can be added to the start time
    STARTTIME_QUARTERS = 6 * 4

    def get_start_time(self):
        """The time of day the Scanner should be automatically started."""
        # add (minutes|hours) in intervals of 15m depending on `pk`, so each
        # scheduled job start at different times after 18h00m
        added_minutes = 15 * (self.pk % self.STARTTIME_QUARTERS)
        added_hours = int(added_minutes / 60)
        added_minutes -= added_hours * 60
        return self.FIRST_START_TIME.replace(
            hour=self.FIRST_START_TIME.hour + added_hours,
            minute=self.FIRST_START_TIME.minute + added_minutes
        )

    @classmethod
    def modulo_for_starttime(cls, time):
        """Convert a datetime.time object to the corresponding modulo value.

        The modulo value can be used to search the database for scanners that
        should be started at the given time by filtering a query with:
            (WebScanner.pk % WebScanner.STARTTIME_QUARTERS) == <modulo_value>
        """
        if(time < cls.FIRST_START_TIME):
            return None
        hours = time.hour - cls.FIRST_START_TIME.hour
        minutes = 60 * hours + time.minute - cls.FIRST_START_TIME.minute
        return int(minutes / 15)

    @property
    def display_name(self):
        """The name used when displaying the scanner on the web page."""
        return "WebScanner '%s'" % self.name

    def __str__(self):
        """Return the name of the scanner."""
        return self.name

    def local_or_rules(self) -> list:
        """Returns a list of OR rules specific for the scanner model
        """
        return []

    def local_and_rules(self) -> list:
        """Returns a list of AND rules specific for the scanner model
        """
        return []

    def local_all_rules(self) -> list:
        """Returns a list of ALL rules specific for the scanner model
        """
        return []

    def run(self, user=None):  # noqa: CCR001
        """Schedules a scan to be run by the pipeline. Returns the scan tag of
        the resulting scan on success.

        An exception will be raised if the underlying source is not available,
        and a pika.exceptions.AMQPError (or a subclass) will be raised if it
        was not possible to communicate with the pipeline."""
        now = time_now()

        # Create a new engine2 scan specification
        rule = OrRule.make(
                *[r.make_engine2_rule()
                  for r in self.rules.all().select_subclasses()])

        try:
            filter_rule = OrRule.make(
                *[er.make_engine2_rule()
                  for er in self.exclusion_rules.all().select_subclasses()])
        except ValueError:
            filter_rule = None

        configuration = {}

        prerules = []
        if self.do_last_modified_check:
            last = self.e2_last_run_at
            if last:
                prerules.append(LastModifiedRule(last))

        if self.do_ocr:
            # If we are doing OCR, then filter out any images smaller than
            # 128x32 (or 32x128)...
            cr = make_if(
                    HasConversionRule(OutputType.ImageDimensions),
                    DimensionsRule(
                            width_range=range(32, 16385),
                            height_range=range(32, 16385),
                            min_dim=128),
                    True)
            prerules.append(cr)
        else:
            # ... and, if we're not, then skip all of the image files
            configuration["skip_mime_types"] = ["image/*"]

        # append any model-specific rules. Order matters!
        # AllRule will evaluate all rules, no matter the outcome of current rule
        # AndRule will only evaluate next rule, if current rule have match
        # OrRule will stop evaluating as soon as one rule have match
        rule = AllRule.make(*self.local_all_rules(), rule)
        rule = OrRule.make(*self.local_or_rules(), rule)
        rule = AndRule.make(*self.local_and_rules(), rule)

        # prerules includes: do_ocr, LastModifiedRule
        rule = AndRule.make(*prerules, rule)

        scan_tag = messages.ScanTagFragment(
                time=now,
                user=user.username if user else None,
                scanner=messages.ScannerFragment(
                        pk=self.pk,
                        name=self.name,
                        test=self.only_notify_superadmin),
                organisation=messages.OrganisationFragment(
                        name=self.organization.name,
                        uuid=self.organization.uuid))

        # Build ScanSpecMessages for all Sources
        message_template = messages.ScanSpecMessage(
            scan_tag=scan_tag, rule=rule, configuration=configuration,
            filter_rule=filter_rule, source=None, progress=None)
        outbox = []
        source_count = 0
        uncensor_map = {}
        for source in self.generate_sources():
            uncensor_map[source.censor()] = source
            outbox.append((
                settings.AMQP_PIPELINE_TARGET,
                message_template._replace(source=source)))
            source_count += 1

        if source_count == 0:
            raise ValueError(f"{self} produced 0 explorable sources")

        # Also build ConversionMessages for the objects that we should try to
        # scan again (our pipeline_collector is responsible for eventually
        # deleting these reminders)
        message_template = messages.ConversionMessage(
                scan_spec=message_template,
                handle=None,
                progress=messages.ProgressFragment(
                    rule=None,
                    matches=[]))
        for reminder in self.checkups.iterator():
            rh = reminder.handle
            if rh.base_handle.source not in uncensor_map:
                # This checkup refers to a Source that we no longer care about
                # (for example, an account that's been removed from the scan).
                # Delete it
                reminder.delete()
                continue
            else:
                rh = rh.remap(uncensor_map)

            # XXX: we could be adding LastModifiedRule twice
            ib = reminder.interested_before
            rule_here = AndRule.make(
                    LastModifiedRule(ib) if ib else True,
                    rule)
            outbox.append((settings.AMQP_CONVERSION_TARGET,
                           message_template._deep_replace(
                               scan_spec__source=rh.source,
                               handle=rh,
                               progress__rule=rule_here)))

        self.e2_last_run_at = self.get_last_successful_run_at()
        self.save()

        # OK, we're committed now! Create a model object to track the status of
        # this scan...
        ScanStatus.objects.create(
                scanner=self, scan_tag=scan_tag.to_json_object(),
                last_modified=timezone.now(), total_sources=source_count,
                total_objects=self.checkups.count())

        # ... and dispatch the scan specifications to the pipeline
        with PikaPipelineThread(
                write={queue for queue, _ in outbox}) as sender:
            for queue, message in outbox:
                sender.enqueue_message(queue, message.to_json_object())
            sender.enqueue_stop()
            sender.start()
            sender.join()

        logger.info(
            "Scan submitted",
            scan=self,
            pk=self.pk,
            scan_type=self.get_type(),
            organization=self.organization,
            rules=rule.presentation,
        )
        return scan_tag.to_json_object()

    def get_last_successful_run_at(self) -> datetime:
        query = ScanStatus.objects.filter(scanner=self)
        finished = (e for e in query if e.finished)
        last = max(finished, key=lambda e: e.last_modified, default=None)
        return last.last_modified if last else None

    def generate_sources(self) -> Iterator[Source]:
        """Yields one or more engine2 Sources corresponding to the target of
        this Scanner."""
        # (this can't use the @abstractmethod decorator because of metaclass
        # conflicts with Django, but subclasses should override this method!)
        raise NotImplementedError("Scanner.generate_sources")
        yield from []

    class Meta:
        abstract = False
        ordering = ['name']


class ScheduledCheckup(models.Model):
    """A ScheduledCheckup is a reminder to the administration system to test
    the availability of a specific Handle in the next scan.

    These reminders serve two functions: to make sure that objects that were
    transiently unavailable will eventually be included in a scan, and to make
    sure that the report module has a chance to resolve matches associated with
    objects that are later removed."""

    handle_representation = JSONField(verbose_name="Reference")
    # The handle to test again.
    interested_before = models.DateTimeField(null=True)
    # The Last-Modified cutoff date to attach to the test.
    scanner = models.ForeignKey(Scanner, related_name="checkups",
                                verbose_name="Tilknyttet scannerjob",
                                on_delete=models.CASCADE)
    # The scanner job that produced this handle.

    @property
    def handle(self):
        return Handle.from_json_object(self.handle_representation)


class ScanStage(Enum):
    INDEXING = 0
    INDEXING_SCANNING = 1
    SCANNING = 2
    EMPTY = 3


class AbstractScanStatus(models.Model):
    """
    Abstract base class for models relating to the status of a scanner job.
    """

    total_sources = models.IntegerField(
        verbose_name=_("total sources"),
        default=0,
    )

    explored_sources = models.IntegerField(
        verbose_name=_("explored sources"),
        default=0,
    )

    total_objects = models.IntegerField(
        verbose_name=_("total objects"),
        default=0,
    )

    scanned_objects = models.IntegerField(
        verbose_name=_("scanned objects"),
        default=0,
    )

    scanned_size = models.BigIntegerField(
            verbose_name=_("size of scanned objects"),
            default=0,
    )

    message = models.TextField(
        blank=True,
        verbose_name='message',
    )

    status_is_error = models.BooleanField(
        default=False,
    )

    @property
    def stage(self) -> int:
        # Workers have not begun scanning any objects yet
        if self.fraction_scanned is None:
            if self.explored_sources >= 0 and self.fraction_explored < 1.0:
                # The explorer is definitely running
                if self.scanned_objects == 0:
                    # The explorer is running, but the scanner is waiting
                    return ScanStage.INDEXING
                # The explorer and worker are running in parallel
                return ScanStage.INDEXING_SCANNING
            elif self.fraction_explored == 1.0:
                # The explorer has finished and did not find any objects
                return ScanStage.EMPTY

        # Workers are scanning objects. Everything is good.
        return ScanStage.SCANNING

    @property
    def finished(self) -> bool:
        return self.fraction_explored == 1.0 and self.fraction_scanned == 1.0

    @property
    def fraction_explored(self) -> float:
        """Returns the fraction of the sources in this scan that has been
        explored, or None if this is not yet computable."""
        if self.total_sources > 0:
            return (self.explored_sources or 0) / self.total_sources
        else:
            return None

    @property
    def fraction_scanned(self) -> float:
        """Returns the fraction of this scan that has been scanned, or None if
        this is not yet computable."""
        if self.fraction_explored == 1.0 and self.total_objects > 0:
            return (self.scanned_objects or 0) / self.total_objects
        else:
            return None

    class Meta:
        abstract = True


class ScanStatus(AbstractScanStatus):
    """A ScanStatus object collects the status messages received from the
    pipeline for a given scan."""

    last_modified = models.DateTimeField(
        verbose_name=_("last modified"),
        default=timezone.now,
    )

    scan_tag = JSONField(
        verbose_name=_("scan tag"),
        unique=True,
    )

    scanner = models.ForeignKey(
        Scanner,
        related_name="statuses",
        verbose_name=_("associated scanner job"),
        on_delete=models.CASCADE,
    )

    resolved = models.BooleanField(
        verbose_name=_("resolved"),
        default=False
    )

    @property
    def estimated_completion_time(self) -> datetime.datetime:
        """Returns the linearly interpolated completion time of this scan
        based on the return value of ScannerStatus.fraction_scanned (or None,
        if that function returns None).

        Note that the return value of this function is only meaningful if
        fraction_scanned is less than 1.0: at that point, it always returns the
        current time."""
        fraction_scanned = self.fraction_scanned
        if (fraction_scanned is not None
                and fraction_scanned >= settings.ESTIMATE_AFTER):
            start = self.start_time
            so_far = time_now() - start
            total_duration = so_far / fraction_scanned
            return start + total_duration
        else:
            return None

    @property
    def start_time(self) -> datetime.datetime:
        """Returns the start time of this scan."""
        return messages.ScanTagFragment.from_json_object(self.scan_tag).time

    class Meta:
        verbose_name = _("scan status")
        verbose_name_plural = _("scan statuses")

        indexes = [
            models.Index(
                    fields=("scanner", "scan_tag",),
                    name="ss_pc_lookup"),
        ]


@receiver(post_delete)
def post_delete_callback(sender, instance, using, **kwargs):
    """Signal handler for post_delete. Requests that all running pipeline
    components blacklist and ignore the scan tag of the now-deleted scan."""
    if not isinstance(instance, ScanStatus):
        return

    msg = messages.CommandMessage(
            abort=messages.ScanTagFragment.from_json_object(
                    instance.scan_tag))
    with PikaPipelineThread() as p:
        p.enqueue_message(
                "", msg.to_json_object(),
                "broadcast", priority=10)
        p.enqueue_stop()
        p.run()


class ScanStatusSnapshot(AbstractScanStatus):
    """
    Snapshot of a ScanStatus object, where the attributes of ScanStatus
    are copied and stored for analysis.
    """

    scan_status = models.ForeignKey(
        ScanStatus,
        on_delete=models.CASCADE
    )

    time_stamp = models.DateTimeField(
        verbose_name=_("timestamp"),
        default=timezone.now,
    )

    class Meta:
        verbose_name = _("scan status snapshot")
        verbose_name_plural = _("scan status snapshots")
