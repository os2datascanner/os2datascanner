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
import re

from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models
from django.utils.translation import ugettext_lazy as _

from os2datascanner.projects.admin.core.models import utilities

from .broadcasted_mixin import Broadcasted

# Kept here to ensure it compiles only once
_sid_regex = re.compile('^S-1-\d+(-\d+){0,15}$')


def validate_sid(value):
    if not _sid_regex.match(value):
        raise ValidationError(
            _("%(value)s is not a valid SID"),
            params={"value": value})


def validate_generic(_):
    pass


class AliasType(utilities.ModelChoiceEnum):
    """Enumeration of Alias types and their respective validators."""
    SID = 'SID', _('SID'), validate_sid
    EMAIL = 'email', _('email'), validate_email
    # Generic is used for unspecified aliases; dummy validator always passes
    GENERIC = 'generic', _('generic'), validate_generic

    def __new__(cls, value, label, validator):
        obj = utilities._new_obj_with_value_and_label(cls, value, label)
        obj.validator = validator
        return obj

    def check(self, value):
        self.validator(value)


class Alias(Broadcasted, models.Model):
    """Represent an alias of a given type for a given Account.

    An Alias is a connection between a labelled item of identifying information
    and an Account. Aliases are broadcasted to the OS2datascanner Report module
    and used to assign matches to relevant user accounts.

    An Account may have several Aliases of the same type.
    """
    uuid = models.UUIDField(
        default=uuid4,
        primary_key=True,
        editable=False,
        verbose_name=_('alias ID'),
    )
    account = models.ForeignKey(
        'Account',
        on_delete=models.CASCADE,
        related_name='aliases',
        verbose_name=_('account'),
    )
    _alias_type = models.CharField(
        max_length=32,
        db_column='alias_type',
        db_index=True,
        choices=AliasType.choices(),
        verbose_name=_('alias type'),
    )
    value = models.CharField(
        max_length=256,
        verbose_name=_('value')
    )

    @property
    def alias_type(self):
        return AliasType(self._alias_type)

    @alias_type.setter
    def alias_type(self, enum):
        self._alias_type = enum.value

    class Meta:
        verbose_name = _('alias')
        verbose_name_plural = _('aliases')

    def __str__(self):
        format_string = _('Alias ({type}) for {account_user}: {value}')
        return format_string.format(
            type=self.alias_type.label,
            account_user=self.account.username,
            value=self.value,
        )

    def __repr__(self):
        f_str = "<{cls}: {value} ({type}) for {account} (Account) - {uuid}>"
        return f_str.format(
            cls=self.__class__.__name__,
            account=self.account_id,
            type=self.alias_type.value,
            value=self.value,
            uuid=self.uuid,
        )

    def clean(self):
        """
        Validate instance data.

        In addition to the functionality of Model.clean(), this implementation
        validates the alias value against the requirements for the alias type.
        """
        super().clean()
        if self.value:
            self.alias_type.check(self.value)
