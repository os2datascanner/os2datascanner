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

from django.db import models
from django.utils.translation import ugettext_lazy as _

from mptt.models import TreeForeignKey

from os2datascanner.projects.admin.core.models import ModelChoiceEnum
from os2datascanner.projects.admin.import_services.models import Imported

from .broadcasted_mixin import Broadcasted


class Role(ModelChoiceEnum):
    """Enumeration of distinguished positions in organizations

    Members are defined by a (value, label) tuple to support translation of
    choice labels.
    """
    EMPLOYEE = ('employee', _('employee'))
    MANAGER = ('manager', _('manager'))
    DPO = ('dpo', _('data protection officer'))


class Position(Imported, Broadcasted, models.Model):
    # TODO: #43095
    account = models.ForeignKey(
        'Account',
        on_delete=models.CASCADE,
        related_name='positions',
        verbose_name=_('account'),
    )
    unit = TreeForeignKey(
        'OrganizationalUnit',
        on_delete=models.CASCADE,
        verbose_name='organizational unit',
    )
    role = models.CharField(
        max_length=30,
        choices=Role.choices(),
        null=False,
        blank=False,
        default=Role.EMPLOYEE.value,
        db_index=True,
    )

    class Meta:
        verbose_name = _('position')
        verbose_name_plural = _('positions')

    def __str__(self):
        format_str = _("{cls}: {account} ({role}) at {unit}")
        cls = _(self.__class__.__name__.lower()).capitalize()
        account = self.account
        role = Role(self.role).label
        unit = self.unit.name
        return format_str.format(account=account, role=role, unit=unit, cls=cls)

    def __repr__(self):
        cls = self.__class__.__name__
        account = self.account
        role = self.role
        unit = self.unit
        return f"<{cls}: {account} (account) is {role} at {unit} (unit)>"
