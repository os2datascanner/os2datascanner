from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class GrantsConfig(AppConfig):
    name = 'os2datascanner.projects.admin.grants'
    label = 'grants'
    verbose_name = _('grants')
    default = True
