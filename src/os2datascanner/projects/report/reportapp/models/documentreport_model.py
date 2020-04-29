from typing import NamedTuple

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import JSONField

from os2datascanner.engine2.pipeline.messages import MatchesMessage


class DocumentReport(models.Model):
    path = models.CharField(max_length=2000, verbose_name="Path")
    # It could be that the meta data should not be part of the jsonfield...
    data = JSONField(null=True)

    def _str_(self):
        return self.path

    @property
    def matches(self):
        matches = self.data.get("matches")
        return MatchesMessage.from_json_object(matches) if matches else None

    resolution_choices = (
        (0, "Andet"),
        (1, "Redigeret"),
        (2, "Flyttet"),
        (3, "Slettet"),
    )

    resolution_status = models.IntegerField(choices=resolution_choices,
                                            null=True, blank=True,
                                            verbose_name="Håndteringsstatus")
    custom_resolution_status = models.CharField(max_length=1024, blank=True,
                                                verbose_name="Begrundelse")

    def clean(self):
        if self.resolution_status == 0:
            if not self.custom_resolution_status:
                raise ValidationError(
                        {
                            "resolution_status":
                                    "Resolution status 0 requires an"
                                    " explanation"
                        })
        elif self.custom_resolution_status:
            raise ValidationError(
                    {
                        "custom_resolution_status":
                                "Explanations can only be associated with"
                                " resolution status 0"
                    })

    class Meta:
        verbose_name_plural = "Document reports"
