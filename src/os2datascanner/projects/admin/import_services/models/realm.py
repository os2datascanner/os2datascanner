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

from .exported_mixin import Exported


class Realm(Exported, models.Model):
    realm_id = models.SlugField(
        allow_unicode=True,
        primary_key=True,
        verbose_name=_('realm id'),
    )
    organization = models.OneToOneField(
        'organizations.Organization',
        on_delete=models.PROTECT,  # TODO: 43163
        verbose_name=_('organization'),
    )

    class Meta:
        verbose_name = _('Keycloak realm')
        verbose_name_plural = _('Keycloak realms')

    def __str__(self):
        return self.realm_id

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.realm_id}>"
