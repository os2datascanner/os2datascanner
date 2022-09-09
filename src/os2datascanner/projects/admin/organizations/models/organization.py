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

from functools import reduce
from django.db import models
from django.utils.translation import ugettext_lazy as _

from os2datascanner.projects.admin.adminapp.models.scannerjobs.scanner import ScanStatus, Scanner
from .broadcasted_mixin import Broadcasted

from os2datascanner.core_organizational_structure.models import Organization as Core_Organization


class Organization(Core_Organization, Broadcasted):
    """ Core logic lives in the core_organizational_structure app.
        Additional specific logic can be implemented here. """

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

    def natural_key(self):
        return (self.uuid, self.name)

    @property
    def scanners_not_running(self) -> bool:
        def not_running(scanner):
            all_statuses = ScanStatus.objects.filter(scanner=scanner)
            latest = all_statuses.latest('last_modified') if all_statuses else None
            return latest.is_not_running if latest else True

        scanners = Scanner.objects.filter(organization=self)
        if scanners:
            return reduce(lambda a, b: a and b,
                          [not_running(scanner) for scanner in scanners])
        else:
            return True
