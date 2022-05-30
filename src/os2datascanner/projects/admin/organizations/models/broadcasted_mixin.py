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

from enum import Enum

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from django.core.serializers import serialize

from os2datascanner.projects.admin.adminapp.signals import ModelChangeEvent
from os2datascanner.projects.admin.adminapp.signals import publish_events


class Broadcasted:
    """Abstract base class for objects for which changes should be broadcasted.

    Implements a default JSON-serializer to ensure all implementing classes can
    be serialized to JSON format.
    """

    class Meta:
        abstract = True

    def to_json_object(self):
        """Return object serialized to JSON format."""
        return serialize('json', [self], use_natural_foreign_keys=True)


# TODO: consider expanding with publication functionality when moving away from signals
class EventType(Enum):
    OBJ_CREATE = 'object_create'
    OBJ_UPDATE = 'object_update'
    OBJ_DELETE = 'object_delete'


# TODO: change to avoid using save/delete-signals as they are not called on bulk actions
# Initial implementation using existing functionality:
@receiver(post_save)
def post_save_broadcast(sender, instance, **kwargs):
    if not isinstance(instance, Broadcasted):
        return
    event_type = (EventType.OBJ_CREATE if kwargs.get('created', None)
                  else EventType.OBJ_UPDATE)
    event = ModelChangeEvent(event_type.value, sender, instance)
    publish_events([event])


@receiver(post_delete)
def post_delete_broadcast(sender, instance, **kwargs):
    if not isinstance(instance, Broadcasted):
        return
    event = ModelChangeEvent(EventType.OBJ_DELETE.value, sender, instance)
    publish_events([event])
