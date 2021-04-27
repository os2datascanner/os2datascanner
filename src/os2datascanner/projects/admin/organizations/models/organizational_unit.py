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

from mptt.models import MPTTModel, TreeForeignKey

from os2datascanner.projects.admin.import_services.models import Imported

from .broadcasted_mixin import Broadcasted


class OrganizationalUnit(MPTTModel, Broadcasted, Imported):
    """Represents a fragment of an organizational hierarchy.

    An OrganizationalUnit typically represents a department or a product team.
    The hierarchy is built through the parent reference, and represents the
    organizational structure of a given organization.
    """

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
        verbose_name=_('UUID'),
    )

    name = models.CharField(
        max_length=256,
        verbose_name=_('name'),
    )
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('parent unit'),
    )

    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )

    class Meta:
        verbose_name = _('organizational unit')
        verbose_name_plural = _('organizational units')

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name} ({self.uuid})>"
