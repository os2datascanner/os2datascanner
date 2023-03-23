from os2datascanner.utils.system_utilities import time_now


class BulkBroadCastEvent:
    publisher = "admin"

    def __init__(self, event_type: str):
        self.event_type = event_type
        self.time = time_now().isoformat()

    def to_json_object(self) -> dict:
        return {
            "time": self.time,
            "type": self.event_type,
            "publisher": self.publisher
        }


class BulkCreateEvent(BulkBroadCastEvent):
    """
    Class for constructing create event messages that can be published through RabbitMQ.
    Provided dict will be used as "classes" and should conform to below structure.
    {
        "time": "<time>",
        "type": "bulk_event_create",
        "publisher": "admin",
        "classes": {
            "Account": "[<serialized objects>]",
            "Alias": "[<serialized objects>]",
            "OrganizationalUnit": "[<serialized objects>]",
            "Position": "[<serialized objects>]",
            "Organization": "[<serialized objects>]"
        }
    }
    """

    def __init__(self, classes: dict):
        super().__init__("bulk_event_create")
        self.classes = classes

    def to_json_object(self) -> dict:
        return super().to_json_object() | {
            "classes": self.classes
        }


class BulkUpdateEvent(BulkBroadCastEvent):
    """
    Class for constructing update event messages that can be published through RabbitMQ.
    Provided dict will be used as "classes" and should conform to below structure.
    {
        "time": "<time>",
        "type": "bulk_event_update",
        "publisher": "admin",
        "classes": {
            "Account": "[<serialized objects>]",
            "Alias": "[<serialized objects>]",
            "OrganizationalUnit": "[<serialized objects>]",
            "Position": "[<serialized objects>]",
            "Organization": "[<serialized objects>]"
        }
    }
    """

    def __init__(self, classes: dict):
        super().__init__("bulk_event_update")
        self.classes = classes

    def to_json_object(self) -> dict:
        return super().to_json_object() | {
            "classes": self.classes
        }


class BulkDeleteEvent(BulkBroadCastEvent):
    """
    Class for constructing delete event messages that can be published through RabbitMQ.
    Provided dict will be used as "classes" and should conform to below structure.
    {
        "time": "<time>",
        "type": "bulk_event_delete",
        "publisher": "admin",
        "classes": {
            "Account": "[<list of primary keys>]",
            "Alias": "[<list of primary keys>]",
            "OrganizationalUnit": "[<list of primary keys>]",
            "Position": "[<list of primary keys>]",
            "Organization": "[<list of primary keys>]"
        }
    }
    """

    def __init__(self, classes: dict):
        super().__init__("bulk_event_delete")
        self.classes = classes

    def to_json_object(self) -> dict:
        return super().to_json_object() | {
            "classes": self.classes
        }
