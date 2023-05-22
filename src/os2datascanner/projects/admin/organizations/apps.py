from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OrganizationsConfig(AppConfig):
    name = 'os2datascanner.projects.admin.organizations'
    label = 'organizations'
    verbose_name = _('organizations')
