import logging
import warnings

from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from os2datascanner.utils.test_helpers import in_test_environment
from os2datascanner.utils.system_utilities import time_now
from os2datascanner.engine2.pipeline.utilities.pika import PikaPipelineThread

logger = logging.getLogger(__name__)


ppt = None


def get_pika_thread() -> PikaPipelineThread:
    """Returns a persistent PikaPipelineThread instance to be used when sending
    event broadcasts, creating (or recreating) one if necessary."""
    global ppt
    if (not ppt  # first call
            or not ppt.ident  # thread never started(?)
            or not ppt.is_alive()):  # thread finished
        ppt = PikaPipelineThread(write=[settings.AMQP_EVENTS_TARGET])
        ppt.daemon = True
        ppt.start()
    return ppt


class ModelChangeEvent():
    publisher = "admin"

    def __init__(self, event_type, model_class, instance, meta=None):

        if meta is None:
            meta = {}

        self.event_type = event_type
        self.model_class = model_class
        self.instance = instance
        self.meta = meta
        self.time = time_now().isoformat()

    def to_json_object(self):
        return {
            "time": self.time,
            # Event type (one of object_create, object_update, object_delete)
            "type": self.event_type,
            # Publisher ID the service
            "publisher": self.publisher,
            # The type of model
            "model_class": self.instance.__class__.__name__,
            # The actual model (JSON-representation using to_json_object())
            "instance": self.instance.to_json_object()
            if hasattr(self.instance, "to_json_object") and callable(self.instance.to_json_object)
            else {"error": "missing to_json_object() method"}, "meta": self.meta
        }


def publish_events(events):
    """Publishes events using the configured queue (AMQP_EVENTS_TARGET)"""
    try:
        # Don't publish events if we appear to be running in a test environment
        if in_test_environment():
            warnings.warn(
                    "running in a test environment; "
                    "suppressing RabbitMQ events", RuntimeWarning)
            return

        queue = settings.AMQP_EVENTS_TARGET
        ppt = get_pika_thread()

        for event in events:
            json_event = event.to_json_object()
            ppt.enqueue_message(queue, json_event)
            logger.debug("Published to {0}: {1}".format(queue, json_event))

        ppt.synchronise()
    except Exception as e:
        # log the error
        logger.error("Could not publish event. Error: " + format(e))


def event_broadcast_enabled(obj):
    """Determine whether event broadcasting is enabled for a given object"""
    try:
        enabled = obj.DatascannerMeta.broadcast_change_events
        return enabled
    except AttributeError:
        return False


@receiver(post_save)
def post_save_callback(**kwargs):
    """Signal receiver for post_save - publishes events when objects are saved"""
    if not event_broadcast_enabled(kwargs.get('instance')):
        return

    event = ModelChangeEvent('object_create' if kwargs.get("created") else 'object_update',
                             kwargs.get('sender'),
                             kwargs.get('instance'))
    publish_events([event])


@receiver(post_delete)
def post_delete_callback(**kwargs):
    """Signal receiver for post_delete - publishes events when objects are deleted"""
    if not event_broadcast_enabled(kwargs.get('instance')):
        return

    event = ModelChangeEvent('object_delete', kwargs.get('sender'), kwargs.get('instance'))
    publish_events([event])
