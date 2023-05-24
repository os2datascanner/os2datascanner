from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CoreOrganizationalStructureConfig(AppConfig):
    name = 'os2datascanner.core_organizational_structure'
    label = 'core_organizational_structure'
    verbose_name = _('core_organizational_structure')
    default = True
