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
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from os2datascanner.core_organizational_structure.models import Alias as Core_Alias
from os2datascanner.core_organizational_structure.models.aliases import AliasType, \
    validate_regex_SID  # noqa


class Alias(Core_Alias):
    """ Core logic lives in the core_organizational_structure app. """

    # For historical reasons we overwrite this field and set it to not be PK.
    # In the admin module (and core_org), it is the PK of aliases. We need it for synchronization
    # purposes - but since reportapp's previous implementation of aliases had an Integer PK,
    # and thus all its relations to documentreports containing that, we keep the PK an int here.
    uuid = models.UUIDField(
        default=uuid4,
        primary_key=False,
        editable=False,
        verbose_name=_('alias ID'),
    )

    user = models.ForeignKey(User, null=False, verbose_name=_('user'),
                             on_delete=models.CASCADE, related_name="aliases")

    # TODO: In the future, we want to use "account" instead of django's User objects.
    # However, for now, we don't - hence this field is nullable.
    account = models.ForeignKey(
        'Account',
        on_delete=models.CASCADE,
        related_name='aliases',
        verbose_name=_('account'),
        blank=True,
        null=True
    )

    @property
    def key(self):
        return self.value

    def __str__(self):
        format_string = ('Alias ({type}) {value}')
        return format_string.format(
            type=self.alias_type.label,
            value=self.value,
        )
