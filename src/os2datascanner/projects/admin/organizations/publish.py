import logging
import warnings

from django.conf import settings
from os2datascanner.utils.test_helpers import in_test_environment
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

        # Synchronise on the PikaPipelineThread event queue to make sure that
        # the daemon thread doesn't stop before actually /sending/ any messages
        ppt.synchronise(300.0)
    except Exception:
        logger.error("event publication failed", exc_info=True)
