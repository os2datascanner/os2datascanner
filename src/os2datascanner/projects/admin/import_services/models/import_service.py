# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2datascanner is developed by Magenta in collaboration with the OS2 public
# sector open source network <https://os2.eu/>.

from django.db import models
from django.utils.translation import ugettext_lazy as _

from model_utils.managers import InheritanceManager


class ImportService(models.Model):
    """Non-abstract parent class for any import service class.

    An ImportService represents the (optional) external identity management
    system for an Organization. When configured, an ImportService allows the
    OS2datascanner system to import relevant Accounts, OrganizationalUnits and
    Positions from the external system.

    NB! Should not be instantiated on its own! It is kept non-abstract to
    ensure one unifying table in the database, to support the one-to-one
    restriction, which in turn ensures a single source of truth for imports.
    """

    objects = InheritanceManager()

    organization = models.OneToOneField(
        'organizations.Organization',
        primary_key=True,
        on_delete=models.CASCADE,
        verbose_name=_('organization UUID'),
    )

    class Meta:
        verbose_name = _('import service')
        verbose_name_plural = _('import services')

    def __str__(self):
        cls = self.__class__.__name__
        format_string = _("{cls} for {org}")
        return format_string.format(org=self.organization, cls=cls)

    def __repr__(self):
        cls = self.__class__.__name__
        return f"<{cls} for {self.organization_id} (Organization)>"
