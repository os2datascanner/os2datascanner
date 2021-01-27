from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from .role_model import Role

class DataProtectionOfficer(Role):

    class Meta:
        verbose_name = _("DPO")
        verbose_name_plural = _("DPO'er")
