from django.utils.translation import ugettext_lazy as _

from .role_model import Role


class DataProtectionOfficer(Role):

    def filter(self, document_reports):
        return document_reports

    class Meta:
        verbose_name = _("DPO")
        verbose_name_plural = _("DPO'er")
