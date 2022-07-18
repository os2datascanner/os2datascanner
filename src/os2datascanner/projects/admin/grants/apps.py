from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class GrantsConfig(AppConfig):
    name = 'os2datascanner.projects.admin.grants'
    label = 'grants'
    verbose_name = _('grants')
