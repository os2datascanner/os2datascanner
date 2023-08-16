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
from datetime import timedelta
from enum import Enum
import os
from typing import Iterator
import structlog
from statistics import linear_regression

from django.db import models
from django.db.models import F, Q
from django.conf import settings
from django.core.validators import validate_comma_separated_integer_list
from django.db.models import JSONField
from django.db.models.signals import post_delete
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver
from django.utils import timezone

from django.contrib.postgres.indexes import HashIndex

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
from os2datascanner.engine2.pipeline.headers import get_exchange, get_headers
from mptt.models import TreeManyToManyField

from ..rules.rule import Rule
from ..authentication import Authentication


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
        verbose_name=_('name')
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
        verbose_name=_('planned execution')
    )

    do_ocr = models.BooleanField(
        default=False,
        verbose_name=_('scan images')
    )

    do_last_modified_check = models.BooleanField(
        default=True,
        verbose_name=_('check date of last modification'),
    )

    only_notify_superadmin = models.BooleanField(
        default=False,
        verbose_name=_('only notify superadmin'),
    )

    columns = models.CharField(validators=[validate_comma_separated_integer_list],
                               max_length=128,
                               null=True,
                               blank=True
                               )

    rules = models.ManyToManyField(Rule,
                                   blank=True,
                                   verbose_name=_('rules'),
                                   related_name='scanners')

    VALID = 1
    INVALID = 0

    validation_choices = (
        (INVALID, _('Unverified')),
        (VALID, _('Verified')),
    )

    authentication = models.OneToOneField(Authentication,
                                          null=True,
                                          related_name='%(app_label)s_%(class)s_authentication',
                                          verbose_name=_('username'),
                                          on_delete=models.SET_NULL)

    validation_status = models.IntegerField(choices=validation_choices,
                                            default=INVALID,
                                            verbose_name=_('validation status'))

    exclusion_rules = models.ManyToManyField(Rule,
                                             blank=True,
                                             verbose_name=_('exclusion rules'),
                                             related_name='scanners_ex_rules')

    covered_accounts = models.ManyToManyField('organizations.Account',
                                              blank=True,
                                              verbose_name=_('covered accounts'),
                                              related_name='covered_by_scanner')

    def verify(self) -> bool:
        """Method documentation"""
        raise NotImplementedError("Scanner.verify")

    @property
    def needs_revalidation(self) -> bool:
        """Used to check if the url on a form object differs from the
        corresponding field on the model object."""
        return False

    @property
    def schedule_date(self):
        """Find date of next scheduled scanjob"""
        if any(self.schedule.occurrences()):
            return self.schedule.occurrences()[0]

    @property
    def schedule_time(self):
        """Find time of next scheduled scanjob"""
        if any(self.schedule.occurrences()):
            return self.get_start_time()

    # Run error messages
    HAS_NO_RULES = (
        _("The scanner job could not be started because it has no assigned rules.")
    )
    NOT_VALIDATED = (
        _("The scanner job could not be started because it is not validated.")
    )
    ALREADY_RUNNING = (
        _("The scanner job could not be started because it is already running.")
    )

    # First possible start time
    FIRST_START_TIME = datetime.time(hour=19, minute=0)
    # Amount of quarter-hours that can be added to the start time
    STARTTIME_QUARTERS = 5 * 4

    def get_start_time(self):
        """The time of day the Scanner should be automatically started."""
        # add (minutes|hours) in intervals of 15m depending on `pk`, so each
        # scheduled job start at different times after 19h00m
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

    def _construct_scan_tag(self, user=None):
        """Builds a scan tag fragment that describes a scan (started now) under
        this scanner."""
        return messages.ScanTagFragment(
                time=time_now(),
                user=user.username if user else None,
                scanner=messages.ScannerFragment(
                        pk=self.pk,
                        name=self.name,
                        test=self.only_notify_superadmin),
                organisation=messages.OrganisationFragment(
                        name=self.organization.name,
                        uuid=self.organization.uuid))

    def _construct_configuration(self):
        """Builds a configuration dictionary based on the parameters of this
        scanner."""
        return {} if self.do_ocr else {"skip_mime_types": ["image/*"]}

    def _construct_rule(self, force: bool) -> Rule:
        """Builds an object that represents the rules configured for this
        scanner."""
        rule = OrRule.make(
                *[r.make_engine2_rule()
                  for r in self.rules.all().select_subclasses()])

        prerules = []
        if not force and self.do_last_modified_check:
            last = self.get_last_successful_run_at()
            if last:
                prerules.append(LastModifiedRule(last))

        if self.do_ocr:
            # If we're doing OCR, then filter out any images smaller than
            # 128x32 (or 32x128)
            cr = make_if(
                    HasConversionRule(OutputType.ImageDimensions),
                    DimensionsRule(
                            width_range=range(32, 16385),
                            height_range=range(32, 16385),
                            min_dim=128),
                    True)
            prerules.append(cr)

        # append any model-specific rules. Order matters!
        # AllRule will evaluate all rules, no matter the outcome of current rule
        # AndRule will only evaluate next rule, if current rule have match
        # OrRule will stop evaluating as soon as one rule have match
        rule = AllRule.make(*self.local_all_rules(), rule)
        rule = OrRule.make(*self.local_or_rules(), rule)
        rule = AndRule.make(*self.local_and_rules(), rule)

        # prerules includes: do_ocr, LastModifiedRule
        return AndRule.make(*prerules, rule)

    def _construct_filter_rule(self) -> Rule:
        try:
            return OrRule.make(
                *[er.make_engine2_rule()
                  for er in self.exclusion_rules.all().select_subclasses()])
        except ValueError:
            pass
        return None

    def _construct_scan_spec_template(self, user, force: bool) -> (
            messages.ScanSpecMessage):
        """Builds a scan specification template for this scanner. This template
        has no associated Source, so make sure you put one in with the _replace
        or _deep_replace methods before trying to scan with it."""
        rule = self._construct_rule(force)
        filter_rule = self._construct_filter_rule()
        scan_tag = self._construct_scan_tag(user)
        configuration = self._construct_configuration()

        return messages.ScanSpecMessage(
                scan_tag=scan_tag, rule=rule, configuration=configuration,
                filter_rule=filter_rule, source=None, progress=None)

    def _add_sources(
            self, spec_template: messages.ScanSpecMessage,
            outbox: list) -> int:
        """Creates scan specifications, based on the provided scan
        specification template, for every Source covered by this scanner, and
        puts them into the provided outbox list. Returns the number of sources
        added."""
        source_count = 0
        for source in self.generate_sources():
            outbox.append((
                settings.AMQP_PIPELINE_TARGET,
                spec_template._replace(source=source)))
            source_count += 1
        return source_count

    def _add_checkups(
            self, spec_template: messages.ScanSpecMessage,
            outbox: list,
            force: bool,
            queue_suffix=None) -> int:
        """Creates instructions to rescan every object covered by this
        scanner's ScheduledCheckup objects (in the process deleting objects no
        longer covered by one of this scanner's Sources), and puts them into
        the provided outbox list. Returns the number of checkups added."""
        uncensor_map = {
                source.censor(): source for source in self.generate_sources()}

        conv_template = messages.ConversionMessage(
                scan_spec=spec_template,
                handle=None,
                progress=messages.ProgressFragment(
                    rule=None,
                    matches=[]))
        checkup_count = 0
        for reminder in self.checkups.iterator():
            rh = reminder.handle

            # for/else is one of the more obscure Python loop constructs, but
            # it is precisely what we want here: the else clause is executed
            # only when the for loop *isn't* stopped by a break statement
            for handle in rh.walk_up():
                if handle.source in uncensor_map:
                    # One of the Sources that contains this checkup's Handle is
                    # still relevant for us. Abort the walk up the tree
                    break
            else:
                # This checkup refers to a Source that we no longer care about
                # (for example, an account that's been removed from the scan).
                # Delete it
                reminder.delete()
                continue

            rh = rh.remap(uncensor_map)

            # XXX: we could be adding LastModifiedRule twice
            ib = reminder.interested_before
            rule_here = AndRule.make(
                    LastModifiedRule(ib) if ib and not force else True,
                    spec_template.rule)
            outbox.append((settings.AMQP_CONVERSION_TARGET,
                           conv_template._deep_replace(
                               scan_spec__source=rh.source,
                               handle=rh,
                               progress__rule=rule_here),
                           ),)
            checkup_count += 1
        return checkup_count

    def run(
            self, user=None,
            explore: bool = True,
            checkup: bool = True,
            force: bool = False):  # noqa: CCR001
        """Schedules a scan to be run by the pipeline. Returns the scan tag of
        the resulting scan on success.

        If the @explore flag is False, no ScanSpecMessages will be emitted for
        this Scanner's Sources. If the @checkup flag is False, no
        ConversionMessages will be emitted for this Scanner's
        ScheduledCheckups. (If both of these flags are False, then this method
        will have nothing to do and will raise an exception.)

        If the @force flag is True, then no Last-Modified checks will be
        requested, not even for ScheduledCheckup objects.

        An exception will be raised if the underlying source is not available,
        and a pika.exceptions.AMQPError (or a subclass) will be raised if it
        was not possible to communicate with the pipeline."""

        spec_template = self._construct_scan_spec_template(user, force)
        scan_tag = spec_template.scan_tag

        outbox = []

        source_count = 0
        if explore:
            source_count = self._add_sources(spec_template, outbox)

            if source_count == 0:
                raise ValueError(f"{self} produced 0 explorable sources")

        checkup_count = 0
        if checkup:
            checkup_count = self._add_checkups(
                spec_template,
                outbox,
                force,
                queue_suffix=self.organization.name)

        if source_count == 0 and checkup_count == 0:
            raise ValueError(f"nothing to do for {self}")

        # Synchronize the 'covered_accounts'-field with accounts, which are
        # about to be scanned.
        self.sync_covered_accounts()

        self.save()

        # Use the name of an appropriate organization as queue_suffix for
        # headers-based routing.
        queue_suffix = self.organization.name

        # Create a model object to track the status of this scan...
        ScanStatus.objects.create(
                scanner=self, scan_tag=scan_tag.to_json_object(),
                last_modified=scan_tag.time, total_sources=source_count,
                total_objects=checkup_count)

        # ... and dispatch the scan specifications to the pipeline!
        with PikaPipelineThread(
                queue_suffix=queue_suffix,
                write={queue for queue, _ in outbox}) as sender:

            for queue, message in outbox:
                sender.enqueue_message(queue,
                                       message.to_json_object(),
                                       exchange=get_exchange(rk=queue),
                                       **get_headers(organisation=queue_suffix))
            sender.enqueue_stop()
            sender.start()
            sender.join()

        logger.info(
            "Scan submitted",
            scan=self,
            pk=self.pk,
            scan_type=self.get_type(),
            organization=self.organization,
            rules=spec_template.rule.presentation,
        )
        return scan_tag.to_json_object()

    def get_last_successful_run_at(self) -> datetime:
        query = ScanStatus.objects.filter(scanner=self)
        finished = (status for status in query if status.finished)
        last = max(finished, key=lambda status: status.start_time, default=None)
        return last.start_time if last else None

    def generate_sources(self) -> Iterator[Source]:
        """Yields one or more engine2 Sources corresponding to the target of
        this Scanner."""
        # (this can't use the @abstractmethod decorator because of metaclass
        # conflicts with Django, but subclasses should override this method!)
        raise NotImplementedError("Scanner.generate_sources")
        yield from []

    def get_covered_accounts(self):
        """Return all accounts which would be scanned by this scannerjob, if
        run at this moment."""
        # Avoid circular import
        from os2datascanner.projects.admin.organizations.models import Account
        if self.org_unit.exists():
            return Account.objects.filter(units__in=self.org_unit.all())
        else:
            return Account.objects.all()

    def sync_covered_accounts(self):
        """Clears the set of accounts covered by this scanner job and
        repopulates it based on the organisational units to be scanned."""
        self.covered_accounts.clear()
        self.covered_accounts.add(*self.get_covered_accounts())

    def get_stale_accounts(self):
        """Return all accounts, which are included in the scanner's
        'covered_accounts' field, but are not associated with any org units
        linked to the scanner."""
        return self.covered_accounts.difference(self.get_covered_accounts())

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
                                verbose_name=_('connected scanner job'),
                                on_delete=models.CASCADE)
    # The scanner job that produced this handle.

    @property
    def handle(self):
        return Handle.from_json_object(self.handle_representation)

    def __str__(self):
        return f"{self.scanner}: {self.handle} ({self.pk})"

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.handle} ({self.pk}) from {self.scanner}>"

    class Meta:
        indexes = (
            HashIndex(
                    fields=("handle_representation",),
                    name="sc_cc_lookup"),
        )


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
        verbose_name=_('message'),
    )

    status_is_error = models.BooleanField(
        default=False,
    )

    matches_found = models.IntegerField(
        verbose_name=_("matches found"),
        default=0,
        null=True,
        blank=True
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
    def fraction_explored(self) -> float | None:
        """Returns the fraction of the sources in this scan that has been
        explored, or None if this is not yet computable.

        This value is clamped, and can never exceed 1.0."""
        if self.total_sources > 0:
            return min(
                    (self.explored_sources or 0) / self.total_sources, 1.0)
        elif self.explored_sources == 0 and self.total_objects != 0:
            # We've explored zero of zero sources, but there are some objects?
            # This scan must consist only of checkups
            return 1.0
        else:
            return None

    @property
    def fraction_scanned(self) -> float | None:
        """Returns the fraction of this scan that has been scanned, or None if
        this is not yet computable.

        This value is clamped, and can never exceed 1.0."""
        if self.fraction_explored == 1.0 and self.total_objects > 0:
            return min(
                    (self.scanned_objects or 0) / self.total_objects, 1.0)
        else:
            return None

    class Meta:
        abstract = True


def inv_linear_func(y, a, b):
    return (y - b)/a if a != 0 else None


class ScanStatus(AbstractScanStatus):
    """A ScanStatus object collects the status messages received from the
    pipeline for a given scan."""

    _completed_Q = (
            Q(total_objects__gt=0)
            & Q(explored_sources=F('total_sources'))
            & Q(scanned_objects__gte=F('total_objects')))

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
    def estimated_completion_time(self) -> datetime.datetime | None:
        """Returns an estimate of the completion time of the scan, based on a
        linear fit to the last 20% of the existing ScanStatusSnapshot objects."""

        if (self.fraction_scanned is None
                or self.fraction_scanned < settings.ESTIMATE_AFTER):
            return None
        else:
            snapshots = list(ScanStatusSnapshot.objects.filter(
                scan_status=self, total_objects__isnull=False).values(
                "time_stamp", "scanned_objects", "total_objects").order_by("time_stamp"))

            # To give an estimate of completion, the number of snapshots _must_
            # be 2 or more.
            if len(snapshots) < 2:
                return None

            width = 0.2  # Percentage of all data points

            # The window function needs to include at least two points, but it's
            # better to include at least ten, to iron out the worst local
            # phenomena.
            window = max([int(len(snapshots)*width), 10])

            time_data = [(obj.get("time_stamp") - self.start_time).total_seconds()
                         for obj in snapshots[-window:]]
            frac_scanned = [obj.get("scanned_objects")/obj.get("total_objects")
                            for obj in snapshots[-window:]]

            a, b = linear_regression(time_data, frac_scanned)

            try:
                end_time_guess = timedelta(
                    seconds=inv_linear_func(
                        1.0, a, b)) + self.start_time
            except Exception as e:
                logger.exception(
                    f'Exception while calculating end time for scan {self.scanner}: {e}')
                return None

            if end_time_guess > time_now():
                return end_time_guess
            else:
                return None

    @property
    def start_time(self) -> datetime.datetime:
        """Returns the start time of this scan."""
        return messages.ScanTagFragment.from_json_object(self.scan_tag).time
    start_time.fget.short_description = _('Start time')

    class Meta:
        verbose_name = _("scan status")
        verbose_name_plural = _("scan statuses")

        indexes = [
            models.Index(
                    fields=("scanner", "scan_tag",),
                    name="ss_pc_lookup"),
        ]

    def __str__(self):
        return f"{self.scanner}: {self.start_time}"

    @classmethod
    def clean_defunct(cls) -> set['ScanStatus']:
        """Updates all defunct ScanStatus objects to appear as though they
        completed normally. (A defunct ScanStatus is one that's at least 99.5%
        complete but that hasn't received any new status messages in the last
        hour.)

        Returns a set of all the ScanStatus objects modified by this
        function."""
        now = time_now()
        rv = set()
        for ss in cls.objects.exclude(
                cls._completed_Q).filter(
                last_modified__lte=now - timedelta(hours=1)).iterator():
            if (ss.fraction_scanned is not None
                    and ss.fraction_scanned >= 0.995):
                # This ScanStatus is essentially complete but hasn't been
                # updated in the last hour; a status message or two must have
                # gone missing. Mark it as done to avoid cluttering the UI
                logger.warning(
                        "marking defunct ScanStatus as complete",
                        scan_status=ss,
                        total_objects=ss.total_objects,
                        scanned_objects=ss.scanned_objects)
                ss.scanned_objects = ss.total_objects
                rv.add(ss)
                ss.save()
        return rv


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
        on_delete=models.CASCADE,
        related_name="snapshots"
    )

    time_stamp = models.DateTimeField(
        verbose_name=_("timestamp"),
        default=timezone.now,
    )

    def __str__(self):
        return f"{self.scan_status.scanner}: {self.time_stamp}"

    class Meta:
        verbose_name = _("scan status snapshot")
        verbose_name_plural = _("scan status snapshots")
