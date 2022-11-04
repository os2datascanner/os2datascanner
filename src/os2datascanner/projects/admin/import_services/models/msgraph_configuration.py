from django.db import models

from ...grants.models import GraphGrant
from .import_service import ImportService
from .exported_mixin import Exported
from django.utils.translation import ugettext_lazy as _


class MSGraphConfiguration(Exported, ImportService):
    grant = models.ForeignKey(GraphGrant, null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = _("MSGraph configuration")
        verbose_name_plural = _("MSGraph configurations")
