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
from .broadcasted_mixin import Broadcasted

from os2datascanner.core_organizational_structure.models import Organization as Core_Organization


class Organization(Core_Organization, Broadcasted):
    """ Core logic lives in the core_organizational_structure app.
      Additional logic can be implemented here, but currently, none needed, hence we pass. """
    client = models.ForeignKey(
        'core.Client',
        on_delete=models.CASCADE,
        related_name='organizations',
        verbose_name=_('client'),
    )
    slug = models.SlugField(
        max_length=256,
        allow_unicode=True,
        unique=True,
        verbose_name=_('slug'),
    )
