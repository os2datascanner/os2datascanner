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

import os
from typing import Iterator
import datetime
from dateutil import tz
from contextlib import closing
import json
import re

from django.conf import settings
from django.core.validators import validate_comma_separated_integer_list
from django.db import models
from django.contrib.postgres.fields import JSONField

from model_utils.managers import InheritanceManager
from recurrence.fields import RecurrenceField

from os2datascanner.engine2.model.core import Source, SourceManager
from os2datascanner.engine2.rules.meta import HasConversionRule
from os2datascanner.engine2.rules.logical import OrRule, AndRule, make_if
from os2datascanner.engine2.rules.dimensions import DimensionsRule
from os2datascanner.engine2.rules.last_modified import LastModifiedRule
import os2datascanner.engine2.pipeline.messages as messages
from os2datascanner.engine2.conversions.types import OutputType

from ..authentication_model import Authentication
from ..organization_model import Organization
from ..group_model import Group
from ..rules.rule_model import Rule
from ..userprofile_model import UserProfile
from os2datascanner.utils import amqp_connection_manager


base_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


class Scanner(models.Model):

    """A scanner, i.e. a template for actual scanning jobs."""
    objects = InheritanceManager()

    linkable = False

    name = models.CharField(max_length=256, unique=True, null=False,
                            db_index=True,
                            verbose_name='Navn')

    organization = models.ForeignKey(Organization, null=False,
                                     verbose_name='Organisation',
                                     on_delete=models.PROTECT)

    group = models.ForeignKey(Group, null=True, blank=True,
                              verbose_name='Gruppe',
                              on_delete=models.SET_NULL)

    schedule = RecurrenceField(max_length=1024,
                               verbose_name='Planlagt afvikling')

    do_ocr = models.BooleanField(default=False, verbose_name='Scan billeder')

    do_last_modified_check = models.BooleanField(
        default=True,
        verbose_name='Tjek dato for sidste ændring',
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

    recipients = models.ManyToManyField(UserProfile, blank=True,
                                        verbose_name='Modtagere')

    # Spreadsheet annotation and replacement parameters

    # Save a copy of any spreadsheets scanned with annotations
    # in each row where matches were found. If this is enabled and any of
    # the replacement parameters are enabled (e.g. do_cpr_replace), matches
    # will also be replaced with the specified text (e.g. cpr_replace_text).
    output_spreadsheet_file = models.BooleanField(default=False)

    # Replace CPRs?
    do_cpr_replace = models.BooleanField(default=False)

    # Text to replace CPRs with
    cpr_replace_text = models.CharField(max_length=2048, null=True,
                                        blank=True)

    # Replace names?
    do_name_replace = models.BooleanField(default=False)

    # Text to replace names with
    name_replace_text = models.CharField(max_length=2048, null=True,
                                         blank=True)
    # Replace addresses?
    do_address_replace = models.BooleanField(default=False)

    # Text to replace addresses with
    address_replace_text = models.CharField(max_length=2048, null=True,
                                            blank=True)

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

    exclusion_rules = models.TextField(blank=True,
                                       default="",
                                       verbose_name='Ekskluderingsregler')

    e2_last_run_at = models.DateTimeField(null=True)

    def exclusion_rule_list(self):
        """Return the exclusion rules as a list of strings or regexes."""
        REGEX_PREFIX = "regex:"
        rules = []
        for line in self.exclusion_rules.splitlines():
            line = line.strip()
            if line.startswith(REGEX_PREFIX):
                rules.append(re.compile(line[len(REGEX_PREFIX):],
                                        re.IGNORECASE))
            else:
                rules.append(line)
        return rules

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
        " fordi den ingen tilknyttede regler har."
    )
    NOT_VALIDATED = (
        "Scannerjobbet kunne ikke startes," +
        " fordi det ikke er blevet valideret."
    )

    process_urls = JSONField(null=True, blank=True)

    # Booleans for control of scanners run from web service.
    do_run_synchronously = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=True)

    # First possible start time
    FIRST_START_TIME = datetime.time(18, 0)
    # Amount of quarter-hours that can be added to the start time
    STARTTIME_QUARTERS = 6 * 4

    def get_start_time(self):
        """The time of day the Scanner should be automatically started."""
        added_minutes = 15 * (self.pk % Scanner.STARTTIME_QUARTERS)
        added_hours = int(added_minutes / 60)
        added_minutes -= added_hours * 60
        return Scanner.FIRST_START_TIME.replace(
            hour=Scanner.FIRST_START_TIME.hour + added_hours,
            minute=Scanner.FIRST_START_TIME.minute + added_minutes
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

    def run(self, user=None):
        """Schedules a scan to be run by the pipeline. Returns the scan tag of
        the resulting scan on success.

        An exception will be raised if the underlying source is not available,
        and a pika.exceptions.AMQPError (or a subclass) will be raised if it
        was not possible to communicate with the pipeline."""
        now = datetime.datetime.now(tz=tz.gettz()).replace(microsecond=0)

        # Create a new engine2 scan specification
        rule = OrRule.make(
                *[r.make_engine2_rule()
                        for r in self.rules.all().select_subclasses()])

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

        rule = AndRule.make(*prerules, rule)

        scan_tag = {
            'time': now.isoformat(),
            'user': user.username if user else None,
            'scanner': {
                'pk': self.pk,
                'name': self.name
            },
            # Names have a uniqueness constraint, so we can /sort of/ use
            # them as a human-readable primary key for organisations in the
            # report module
            'organisation': self.organization.name,
            'destination': 'pipeline_collector'
        }

        # Check that all of our Sources are runnable, and build
        # ScanSpecMessages for them
        message_template = messages.ScanSpecMessage(scan_tag=scan_tag,
                rule=rule, configuration=configuration, source=None,
                progress=None)
        outbox = []
        for source in self.generate_sources():
            with SourceManager() as sm, closing(source.handles(sm)) as handles:
                next(handles, True)
            outbox.append((settings.AMQP_PIPELINE_TARGET,
                    message_template._replace(source=source)))

        # Also build ConversionMessages for the objects that we should try to
        # scan again
        message_template = messages.ConversionMessage(
                scan_spec=message_template,
                handle=None, progress=messages.ProgressFragment(
                        rule=None,
                        matches=[]))
        for reminder in self.checkups.all():
            ib = reminder.interested_before
            rule_here = AndRule.make(
                    LastModifiedRule(ib) if ib else True,
                    rule)
            outbox.append((settings.AMQP_CONVERSION_TARGET,
                    message_template._deep_replace(
                            scan_spec__source=reminder.handle.source,
                            progress__rule=rule_here)))
        self.checkups.all().delete()

        self.e2_last_run_at = now
        self.save()

        # Dispatch the scan specifications to the pipeline
        queue_name = settings.AMQP_PIPELINE_TARGET
        amqp_connection_manager.start_amqp(queue_name)
        for queue, message in outbox:
            amqp_connection_manager.send_message(
                    queue, json.dumps(message.to_json_object()))
        amqp_connection_manager.close_connection()

        return scan_tag

    def path_for(self, uri):
        return uri

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
    """A ScheduledCheckup is a single-use reminder to the administration system
    to test the availability of a specific Handle in the next scan.

    These reminders serve two functions: to make sure that objects that were
    transiently unavailable will eventually be included in a scan, and to make
    sure that the report module has a chance to resolve matches associated with
    objects that are later removed."""

    handle_representation = JSONField(verbose_name="Reference")
    """The handle to test again."""
    interested_before = models.DateTimeField(null=True)
    """The Last-Modified cutoff date to attach to the test."""
    scanner = models.ForeignKey(Scanner, related_name="checkups",
                                verbose_name="Tilknyttet scannerjob",
                                on_delete=models.CASCADE)
    """The scanner job that produced this handle."""

    @property
    def handle(self):
        return Handle.from_json_object(self.handle_representation)
