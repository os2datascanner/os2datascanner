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

from os2datascanner.utils.model_helpers import ModelFactory
from os2datascanner.core_organizational_structure.models import Account as Core_Account
from os2datascanner.projects.admin.import_services.models import Imported

from .broadcasted_mixin import Broadcasted, post_save_broadcast


class Account(Core_Account, Imported, Broadcasted):
    """ Core logic lives in the core_organizational_structure app.
        Additional specific logic can be implemented here. """

    factory = None

    def natural_key(self):
        return (self.pk, self.username,
                self.organization.uuid, self.organization.name,
                )

    def get_stale_scanners(self):
        """Returns all scanners, which do not cover the account, but still
        contains the account in its 'covered_accounts'-field."""

        # Avoid circular import
        from os2datascanner.projects.admin.adminapp.models.scannerjobs.scanner import Scanner
        stale_scanners = Scanner.objects.filter(
            covered_accounts=self).exclude(
            org_unit__in=self.units.all())
        return stale_scanners


Account.factory = ModelFactory(Account)


@Account.factory.on_create
@Account.factory.on_update
def on_account_created_updated(objects, fields=None):
    for acc in objects:
        post_save_broadcast(None, acc)
