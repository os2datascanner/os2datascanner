from django.utils.translation import ugettext_lazy as _
from django.db import models

from .role import Role


class DataProtectionOfficer(Role):

    contact_person = models.BooleanField(default=False, verbose_name=_("Contact Person"))

    @property
    def url(self):
        return '/statistics/dpo/'

    @property
    def description(self):
        return _("DPO overview")

    def filter(self, document_reports):
        return document_reports

    class Meta:
        verbose_name = _("DPO")
        verbose_name_plural = _("DPOs")
