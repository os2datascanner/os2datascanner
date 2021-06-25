import enum

from django.db import models
from django.db.models.signals import post_save, post_delete
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import JSONField
from django.utils.translation import ugettext_lazy as _
from .organization_model import Organization

from os2datascanner.utils.model_helpers import ModelFactory
from os2datascanner.utils.system_utilities import time_now
from os2datascanner.engine2.pipeline.messages import (
    MatchesMessage, ProblemMessage, MetadataMessage
    )
import structlog

logger = structlog.get_logger(__name__)



class DocumentReport(models.Model):
    factory = None

    scan_time = models.DateTimeField(null=True, db_index=True,
                                            verbose_name=_('scan time'))

    created_timestamp = models.DateTimeField(null=True,
                                             verbose_name=_('created timestamp'))

    organization = models.ForeignKey(Organization,
                                     null=True, blank=True,
                                     verbose_name=_('organization'),
                                     on_delete=models.PROTECT)

    path = models.CharField(max_length=2000, verbose_name=_("path"),
                            db_index=True)
    # It could be that the meta data should not be part of the jsonfield...
    data = JSONField(null=True)

    source_type = models.CharField(max_length=2000,
                                   verbose_name=_("source type"))

    sensitivity = models.IntegerField(null=True, verbose_name=_("sensitivity"))

    probability = models.FloatField(null=True, verbose_name=_("probability"))

    # datasource_last_modified stores when the scanned file/email/element itself, has last been updated.
    # This timestamp is collected during scan and is from the datasource.
    datasource_last_modified = models.DateTimeField(null=True)

    def _str_(self):
        return self.path

    @property
    def matches(self):
        matches = self.data.get("matches")
        return MatchesMessage.from_json_object(matches) if matches else None

    @property
    def problem(self):
        problem = self.data.get("problem")
        return ProblemMessage.from_json_object(problem) if problem else None

    @property
    def metadata(self):
        metadata = self.data.get("metadata")
        return MetadataMessage.from_json_object(metadata) if metadata else None

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

        presentation = type_msg.handle.presentation if type_msg.handle else ""
        return presentation

    @enum.unique
    class ResolutionChoices(enum.Enum):
        # Future simplification note: the behaviour of the enumeration values
        # of this class is modelled on Django 3's model.Choices
        OTHER = 0, "Andet"
        EDITED = 1, "Redigeret"
        MOVED = 2, "Flyttet"
        REMOVED = 3, "Slettet"
        NO_ACTION = 4, "Intet foretaget"

        def __new__(cls, *args):
            obj = object.__new__(cls)
            # models.Choices compatibility: the last element of the enum value
            # tuple, if there is one, is a human-readable label
            obj._value_ = args[0] if len(args) < 3 else args[:-1]
            return obj

        def __init__(self, *args):
            self.label = args[-1] if len(args) > 1 else self.name

        # This is a class *property* in model.Choices, but that would require
        # sinister metaclass sorcery
        @classmethod
        def choices(cls):
            return [(k.value, k.label) for k in cls]

    resolution_status = models.IntegerField(choices=ResolutionChoices.choices(),
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
        now = time_now()

        # If Resolution status goes from not handled to handled - change resolution_time to now
        if self.__resolution_status == None and (self.resolution_status or self.resolution_status == 0):
            self.resolution_time = now

        # Adds a timestamp if it's a new match:
        if not self.pk:
            self.created_timestamp = now

        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = _("document reports")
        ordering = ['-sensitivity', '-probability']


DocumentReport.factory = ModelFactory(DocumentReport)


@DocumentReport.factory.on_create
@DocumentReport.factory.on_update
def on_documentreport_created_or_updated(objects, fields=None):
    from .aliases.alias_model import Alias

    tm = Alias.match_relation.through
    new_objects = []
    for obj in objects:
        # Add DocumentReport to Alias.match_relation, when it's saved to the db.
        try:
            metadata = obj.data['metadata']['metadata'].values()
            value = list(metadata)[0]
            aliases = Alias.objects.select_subclasses()

            for alias in aliases:
                if str(alias) == value:
                    new_objects.append(
                            tm(documentreport_id=obj.pk, alias_id=alias.pk))
        except (KeyError, TypeError):
            logger.info(f"{obj} has no metadata")
    try:
        # TODO: We do not bulk create DocumentReports, and therefore will we always
        #  bulk_create 1 Alias.match_relation at the time. We do not actually
        #  use the bulk functionality.
        tm.objects.bulk_create(new_objects, ignore_conflicts=True)
    except:
        logger.error("Failed to create match_relation", exc_info=True)


# TODO: #43340 (if we need to explicitly delete the instances of the implicit
# model class used by Alias.match_relation, we should also hook DocumentReport.
# factory.on_delete here)
