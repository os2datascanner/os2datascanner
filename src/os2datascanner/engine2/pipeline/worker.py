import logging

from .explorer import message_received_raw as explorer_handler
from .processor import message_received_raw as processor_handler
from .matcher import message_received_raw as matcher_handler
from .tagger import message_received_raw as tagger_handler
from . import messages


logger = logging.getLogger(__name__)


READS_QUEUES = ("os2ds_conversions",)
WRITES_QUEUES = (
    "os2ds_matches",
    "os2ds_checkups",
    "os2ds_problems",
    "os2ds_metadata",
    "os2ds_status",)
PROMETHEUS_DESCRIPTION = "Messages handled by worker"
# Let the Pika background thread aggressively collect tasks. Workers should
# always be doing something -- every centisecond of RabbitMQ overhead is time
# wasted!
PREFETCH_COUNT = 8


def explore(sm, msg):
    for channel, message in explorer_handler(msg, "os2ds_scan_specs", sm):
        if channel == "os2ds_conversions":
            yield from process(sm, message)
        elif channel == "os2ds_scan_specs":
            # Huh? Surely a standalone explorer should have handled this
            logger.warning("worker exploring unexpected nested Source")
            yield from explore(sm, message)
        else:
            yield channel, message


def process(sm, msg):
    for channel, message in processor_handler(msg, "os2ds_conversions", sm):
        if channel == "os2ds_representations":
            yield from match(sm, message)
        elif channel == "os2ds_scan_specs":
            yield from explore(sm, message)
        else:
            yield channel, message


def match(sm, msg):
    for channel, message in matcher_handler(msg, "os2ds_representations", sm):
        if channel == "os2ds_handles":
            yield from tag(sm, message)
        elif channel == "os2ds_conversions":
            yield from process(sm, message)
        else:
            yield channel, message


def tag(sm, msg):
    yield from tagger_handler(msg, "os2ds_handles", sm)


def message_received_raw(body, channel, source_manager):  # noqa: CCR001, E501 too high cognitive complexity
    try:
        for channel, message in process(source_manager, body):
            if channel in WRITES_QUEUES:
                yield (channel, message)
            else:
                logger.error(f"unexpected message to queue {channel}")
    finally:
        message = messages.ConversionMessage.from_json_object(body)
        object_size = 0
        object_type = "application/octet-stream"
        try:
            resource = message.handle.follow(source_manager)
            object_size = resource.get_size().value
            object_type = resource.compute_type()
        except Exception:
            pass
        yield ("os2ds_status", messages.StatusMessage(
                scan_tag=message.scan_spec.scan_tag,
                message="", status_is_error=False,
                object_size=object_size,
                object_type=object_type).to_json_object())


if __name__ == "__main__":
    from .run_stage import _compatibility_main  # noqa
    _compatibility_main("worker")
