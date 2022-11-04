from .import_service import ImportService
from .exported_mixin import Exported
from django.utils.translation import ugettext_lazy as _


class OS2moConfiguration(Exported, ImportService):

    class Meta:
        verbose_name = _("OS2mo configuration")
        verbose_name_plural = _("OS2mo configurations")
