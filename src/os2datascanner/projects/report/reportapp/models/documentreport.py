import enum
from functools import cached_property

from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import JSONField
from django.db.models.functions import Upper
from django.utils.translation import gettext_lazy as _

from os2datascanner.projects.report.organizations.models import Organization
from os2datascanner.utils.system_utilities import time_now
from os2datascanner.engine2.pipeline.messages import (
    MatchesMessage, ProblemMessage, MetadataMessage, ScanTagFragment
)
import structlog

from os2datascanner.projects.report.organizations.models import Alias

logger = structlog.get_logger(__name__)


class DocumentReport(models.Model):
    factory = None

    # Solution created in admin.py, since save() method doesn't work with m2m relations.
    # Changed save_model in admin.py, to make sure m2m relations doesn't get cleared after save
    # noqa Source: https://stackoverflow.com/questions/1925383/issue-with-manytomany-relationships-not-updating-immediately-after-save/1925784#1925784

    alias_relation = models.ManyToManyField(Alias, blank=True,
                                            verbose_name=_('Alias relation'),
                                            related_name='match_relation',
                                            db_table="new_alias_relation")

    scan_time = models.DateTimeField(null=True, db_index=True,
                                     verbose_name=_('scan time'))

    created_timestamp = models.DateTimeField(null=True,
                                             verbose_name=_('created timestamp'))

    last_opened_time = models.DateTimeField(null=True, verbose_name=_('time last opened'))

    organization = models.ForeignKey(Organization,
                                     null=True, blank=True,
                                     verbose_name=_('organization'),
                                     on_delete=models.PROTECT)

    path = models.CharField(max_length=256, verbose_name=_("path"))

    raw_scan_tag = JSONField(null=True)
    raw_matches = JSONField(null=True)
    raw_problem = JSONField(null=True)
    raw_metadata = JSONField(null=True)

    # sort results from a Source. It does not make sense to sort across Sources
    sort_key = models.CharField(
        max_length=256, verbose_name=_("sort key"), db_index=True, default=""
    )

    # the name of the specific resource a handle points to. The equivalent of a #
    # filename
    name = models.CharField(max_length=256, verbose_name=_("name"), default="")

    source_type = models.CharField(max_length=2000,
                                   verbose_name=_("source type"))

    sensitivity = models.IntegerField(null=True, verbose_name=_("sensitivity"))

    probability = models.FloatField(null=True, verbose_name=_("probability"))

    # datasource_last_modified stores when the scanned file/email/element itself,
    #  has last been updated.
    # This timestamp is collected during scan and is from the datasource.
    datasource_last_modified = models.DateTimeField(null=True)

    # Field to store the primary key of the scanner job that this DocumentReport stems from.
    scanner_job_pk = models.IntegerField(null=True)
    # Field to store name of the scanner job that this DocumentReport stems from.
    scanner_job_name = models.CharField(
        max_length=256,
        null=True,
        db_index=True,
    )

    only_notify_superadmin = models.BooleanField(
        default=False,
        verbose_name='Underret kun superadmin',
    )

    owner = models.TextField(
        blank=True,
        null=True,
        db_index=True
    )

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name} ({self.pk})>"

    @cached_property
    def scan_tag(self):
        return ScanTagFragment.from_json_object(self.raw_scan_tag)

    @cached_property
    def matches(self):
        return (MatchesMessage.from_json_object(self.raw_matches)
                if self.raw_matches else None)

    @cached_property
    def problem(self):
        return (ProblemMessage.from_json_object(self.raw_problem)
                if self.raw_problem else None)

    @cached_property
    def metadata(self):
        return (MetadataMessage.from_json_object(self.raw_metadata)
                if self.raw_metadata else None)

    @property
    def presentation(self) -> str:
        """Get the handle presentation"""
        # get the Message. Only one of these will be non-None.
        type_msg = [msg for msg in
                    [self.matches, self.problem, self.metadata] if msg]
        # in case the report is still not updated with the Message, return empty
        # string
        if type_msg == []:
            return ""
        type_msg = type_msg[0]

        presentation = str(type_msg.handle) if type_msg.handle else ""
        return presentation

    def update_opened(self):
        self.last_opened_time = time_now()
        self.save()

    @enum.unique
    class ResolutionChoices(models.IntegerChoices):
        OTHER = 0, _("Other")
        EDITED = 1, _("Edited")
        MOVED = 2, _("Deleted and journalized")
        REMOVED = 3, _("Deleted")
        FALSE_POSITIVE = 4, _("False positive")

    number_of_matches = models.IntegerField(default=0,
                                            verbose_name=_("number of matches"),
                                            db_index=True,)

    resolution_status = models.IntegerField(choices=ResolutionChoices.choices,
                                            null=True, blank=True, db_index=True,
                                            verbose_name=_("resolution status"))

    resolution_time = models.DateTimeField(blank=True, null=True,
                                           verbose_name=_("resolution time"))

    custom_resolution_status = models.CharField(max_length=1024, blank=True,
                                                verbose_name=_("justification"))

    def clean(self):
        self.clean_custom_resolution_status()

    def clean_custom_resolution_status(self):
        self.custom_resolution_status = self.custom_resolution_status.strip()
        if self.resolution_status == 0 and not self.custom_resolution_status:
            raise ValidationError(
                {
                    "custom_resolution_status":
                        "Resolution status 0 requires an"
                        " explanation"
                })

    def __init__(self, *args, **kwargs):
        # TODO: move to property/model method
        super().__init__(*args, **kwargs)
        self.__resolution_status = self.resolution_status

    def save(self, *args, **kwargs):
        # Count and save number of matches
        self.number_of_matches = 0
        # Exclude rules meant for image conversion
        excluded_rules = ["dimensions", "conversion"]
        if self.matches:
            for rule_dict in self.matches.matches:
                if rule_dict.matches and rule_dict.rule.type_label not in excluded_rules:
                    self.number_of_matches += len(rule_dict.matches)

        # If Resolution status goes from not handled to handled - change resolution_time to now
        if self.__resolution_status is None and (
                self.resolution_status or self.resolution_status == 0):
            self.resolution_time = time_now()

        # Adds a timestamp if it's a new match:
        if not self.pk:
            self.created_timestamp = time_now()

        # ensure model field constrains
        if len(old_name := self.name) > 256:
            self.name = self.name[:256]
        if len(old_sort_key := self.sort_key) > 256:
            self.sort_key = self.sort_key[:256]

        super().save(*args, **kwargs)

        # log after save, so self returns the Object pk.
        if len(old_name) > 256:
            logger.info("truncated name before saving", report=self, name=old_name)
        if len(old_sort_key) > 256:
            logger.info("truncated sort_key before saving", report=self,
                        sort_key=self.sort_key)

    class Meta:
        verbose_name_plural = _("document reports")
        ordering = ['-sensitivity', '-probability', 'pk']
        # TODO: Consider if raw_matches__matched index should be removed
        # it's more performant to use number_of_matches
        indexes = [
            models.Index(
                "raw_matches__matched",
                name="documentreport_matched"),
            models.Index(
                fields=("path",),
                name="pc_update_query"),
            # Django implements __iexact, which we use when handling mail
            # aliases, by doing UPPER() on both sides of the expression. Make
            # sure we have an index of that -- otherwise we'll need to
            # recompute it once for every DocumentReport /for every Alias!/
            models.Index(
                Upper("owner"),
                name="alias_creation_query_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["scanner_job_pk", "path"],
                name="unique_scanner_pk_and_path")
        ]
