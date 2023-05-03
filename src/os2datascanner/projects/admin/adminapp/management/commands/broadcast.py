from django.core.management.base import BaseCommand

from ....organizations.broadcast_bulk_events import BulkBroadcastEvent, BulkCreateEvent
from ....organizations.publish import publish_events
from ....organizations.models.organization import OrganizationSerializer
from ....organizations.models.organization import Organization
from ....organizations.utils import get_broadcasted_models
from os2datascanner.core_organizational_structure.utils import get_serializer


class BulkPurgeEvent(BulkBroadcastEvent):
    def __init__(self, classes: list):
        super().__init__("bulk_event_purge")
        self.classes = classes

    def to_json_object(self) -> dict:
        return super().to_json_object() | {
            "classes": self.classes
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
            help="Purge data that stem from an import-job in the report module"
                 "OBS: Does not delete Organization objects!"
        )
        parser.add_argument(
            "--no-org",
            default=False,
            action="store_true",
            help="Exclude Organization in create message"
        )

    def handle(self, *args, purge, no_org, **options):
        broadcasted_models = get_broadcasted_models()

        if purge:  # Delete
            deletion_list = [broadcastable_model.__name__ for broadcastable_model in
                             broadcasted_models if not broadcastable_model == Organization]
            # Publishes a structure of:
            # {
            #     "time": "<>",
            #     "type": "bulk_event_purge",
            #     "publisher": "admin",
            #     "classes": [
            #         "Account",
            #         "Alias",
            #         "OrganizationalUnit",
            #         "Position"
            #     ]
            # }
            print(f"Publishing deletion instructions: \n {deletion_list}")
            event = BulkPurgeEvent(deletion_list)

        else:  # Create
            creation_dict = {}
            for broadcastable_model in broadcasted_models:
                serializer = get_serializer(broadcastable_model)
                serialized_imported = serializer(broadcastable_model.objects.all(), many=True).data
                creation_dict[broadcastable_model.__name__] = serialized_imported

            if not no_org:
                creation_dict["Organization"] = OrganizationSerializer(
                    Organization.objects.all(), many=True).data

            print(f"Publishing creation instructions:\n {creation_dict}")
            # Publishes a structure of:
            # {
            #     "time": "<time>",
            #     "type": "bulk_event_create",
            #     "publisher": "admin",
            #     "classes": {
            #         "Account": "[<serialized objects>]",
            #         "Alias": "[<serialized objects>]",
            #         "OrganizationalUnit": "[<serialized objects>]",
            #         "Position": "[<serialized objects>]",
            #         "Organization": "[<serialized objects>]"
            #     }
            # }
            event = BulkCreateEvent(creation_dict)

        publish_events([event])
