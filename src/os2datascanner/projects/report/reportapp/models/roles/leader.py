from django.utils.translation import ugettext_lazy as _

from .role import Role


class Leader(Role):

    def filter(self, document_reports):
        return document_reports

    class Meta:
        verbose_name = _("leader")
        verbose_name_plural = _("leaders")
