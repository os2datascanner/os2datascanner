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
#

from uuid import uuid4

from django.db import models
from django.utils.translation import ugettext_lazy as _

from os2datascanner.projects.admin.import_services.models import Imported

from .broadcasted_mixin import Broadcasted


class Account(Imported, Broadcasted, models.Model):
    """Represents a known entity in an organizational hierarchy.

    An Account may be related to several OrganizationalUnits within the same
    Organization.

    Note that Accounts are data representations of accounts on other systems
    and as such does not give its corresponding entity access to the
    OS2datascanner administration system.
    """

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
        verbose_name=_('UUID'),
    )
    username = models.CharField(
        max_length=256,
        verbose_name=_('username'),
    )
    first_name = models.CharField(
        max_length=256,
        verbose_name=_('first name'),
    )
    last_name = models.CharField(
        max_length=256,
        verbose_name=_('last name'),
    )
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='user_accounts',
        verbose_name=_('organization'),
    )
    units = models.ManyToManyField(
        'OrganizationalUnit',
        through='Position',
    )

    class Meta:
        verbose_name = _('account')
        verbose_name_plural = _('accounts')

    def __str__(self):
        return self.username

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.username} ({self.uuid})>'
