from django.utils.translation import ugettext_lazy as _

from .role import Role


class Leader(Role):

    @property
    def url(self):
        return '/statistics/leader/'

    @property
    def description(self):
        return _("Leader overview")

    def filter(self, document_reports):
        return document_reports

    class Meta:
        verbose_name = _("leader")
        verbose_name_plural = _("leaders")
