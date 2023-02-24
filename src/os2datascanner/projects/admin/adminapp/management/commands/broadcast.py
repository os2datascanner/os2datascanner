from django.apps import apps

from django.core.management.base import BaseCommand
from django.core.serializers import serialize
from os2datascanner.utils.system_utilities import time_now
from ...signals import publish_events
from ....organizations.models.broadcasted_mixin import Broadcasted
from ....organizations.models.organization import Organization


class BulkBroadCastEvent:
    publisher = "admin"

    def __init__(self, event_type: str, instance: list):
        self.event_type = event_type
        self.instance = instance
        self.time = time_now().isoformat()

    def to_json_object(self) -> dict:
        return {
            "time": self.time,
            "type": self.event_type,
            "publisher": self.publisher,
            "instance": self.instance
        }


class Command(BaseCommand):
    """
        Synchronize Organizational Structure models between Admin and Report module through
        a single message.

        Provided no arguments, will attempt to create what's currently found in the admin module.
        Provided --purge, will delete existing objects. (Only in the report module)
    """

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "-p", "--purge",
            default=False,
            action="store_true",
            help="Purge all data that stem from an import-job in the report module"
        )

    def handle(self, *args, purge, **options):
        def get_broadcasted_models():
            """Return a list of all models that inherit from Broadcasted."""
            models = []
            for model in apps.get_models():
                # We'll only want Organization included in create.
                # Deleting an Org from the report module potentially destroys too much.
                # (Document reports)
                if issubclass(model, Broadcasted) and model is not Organization:
                    models.append(model)
            return models

        broadcasted_models = get_broadcasted_models()

        if purge:  # Delete
            deletion_list = []
            for broadcastable_model in broadcasted_models:
                deletion_list.append(broadcastable_model.__name__)

            # Publishes a structure of:
            # {
            #     "time": "<>",
            #     "type": "object_broadcast_purge",
            #     "publisher": "admin",
            #     "instance": [
            #         "Account",
            #         "Alias",
            #         "OrganizationalUnit",
            #         "Position"
            #     ]
            # }
            event = BulkBroadCastEvent('object_broadcast_purge', deletion_list)

        else:  # Create
            creation_dict = {}
            for broadcastable_model in broadcasted_models:
                serialized_imported = serialize('json', broadcastable_model.objects.all())
                creation_dict[broadcastable_model.__name__] = serialized_imported

            creation_dict["Organization"] = serialize('json', Organization.objects.all())

            # Publishes a structure of:
            # {
            #     "time": "<time>",
            #     "type": "object_broadcast_create",
            #     "publisher": "admin",
            #     "instance": [
            #         {
            #             "Account": "[<serialized objects>]",
            #             "Alias": "[<serialized objects>]",
            #             "OrganizationalUnit": "[<serialized objects>]",
            #             "Position": "[<serialized objects>]",
            #             "Organization": "[<serialized objects>]"
            #         }
            #     ]
            # }
            event = BulkBroadCastEvent('object_broadcast_create', [creation_dict])

        publish_events([event])
