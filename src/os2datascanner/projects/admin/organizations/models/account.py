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


from os2datascanner.core_organizational_structure.models import Account as Core_Account
from os2datascanner.projects.admin.import_services.models import Imported

from .broadcasted_mixin import Broadcasted


class Account(Core_Account, Imported, Broadcasted):
    """ Core logic lives in the core_organizational_structure app.
    Additional logic can be implemented here, but currently, none needed, hence we pass. """

    def natural_key(self):
        return (self.pk, self.username,
                self.organization.uuid, self.organization.name,
                )
