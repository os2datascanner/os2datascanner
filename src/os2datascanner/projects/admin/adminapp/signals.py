from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from inspect import ismethod
from os2datascanner.utils import amqp_connection_manager
import json
import logging
import sys

logger = logging.getLogger(__name__)

class ModelChangeEvent():
    publisher = "admin"

    def __init__(self, event_type, model_class, instance, meta = {}):
        self.event_type = event_type
        self.model_class = model_class
        self.instance = instance
        self.meta = meta


    def to_json_object(self):
        return {
            # Event type (one of object_create, object_update, object_delete)
            "type": self.event_type,
            # Publisher ID the service 
            "publisher": self.publisher,
            # The type of model
            "model_class": self.instance.__class__.__name__,
            # The actual model (JSON-representation using to_json_object())
            "instance": self.instance.to_json_object() 
                            if hasattr(self.instance, "to_json_object") and 
                               ismethod(getattr(self.instance, "to_json_object"))
                            else {"error": "missing to_json_object() method"}
        }


def publish_events(events):
    """Publishes events using the configured queue (AMQP_EVENTS_TARGET)"""
    try:
        queue = settings.AMQP_EVENTS_TARGET
        amqp_connection_manager.start_amqp(queue)
        for event in events:
            json_event = event.to_json_object()
            logger.info("Published to {0}: {1}".format(queue, json_event))
            amqp_connection_manager.send_message(
                queue, json.dumps(json_event))
        amqp_connection_manager.close_connection()
    except Exception as e: 
        # log the error
        logger.error("Could not publish event. Error: "+format(e))


@receiver(post_save)
def post_save_callback(**kwargs):
    """Signal receiver for post_save - publishes events when objects are saved"""
    event = ModelChangeEvent('object_create' if kwargs.get("created") else 'object_update', 
                  kwargs.get('sender'), 
                  kwargs.get('instance'))
    publish_events([event])


@receiver(post_delete)
def post_delete_callback(**kwargs):
    """Signal receiver for post_delete - publishes events when objects are deleted"""
    event = ModelChangeEvent('object_delete', kwargs.get('sender'), kwargs.get('instance'))
    publish_events([event])
