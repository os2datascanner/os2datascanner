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
from os2datascanner.projects.admin.import_services.models import Imported
from os2datascanner.core_organizational_structure.models import Position as Core_Position
from .broadcasted_mixin import Broadcasted, post_save_broadcast


class Position(Core_Position, Imported, Broadcasted):
    """ Core logic lives in the core_organizational_structure app.
        Additional specific logic can be implemented here. """
    factory = None
    pass


Position.factory = ModelFactory(Position)


@Position.factory.on_create
@Position.factory.on_update
def on_account_created_updated(objects, fields=None):
    for pos in objects:
        post_save_broadcast(None, pos)
