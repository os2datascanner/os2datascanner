from typing import NamedTuple

from django.db import models
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

    class Meta:
        verbose_name_plural = "Document reports"
