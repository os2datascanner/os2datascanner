import logging
# from .. import settings


logger = logging.getLogger(__name__)


def get_headers(stage=None, organisation=None, msg=None, rk=None):
    """Gets the relevant basic AMQP properties (headers) for use in PikaPipelineThread.
      This is dependent on the stage/module, the message (msg) and the routing_key (rk)."""

    # We want to be able to configure processes to be very specific about what
    # they consume, so we require that all header patterns match, not just any
    # one of them.
    headers = {"x-match": "all"}

    if organisation:
        # We use the queue_suffix to represent something similar to an organisation,
        # since the engine does not know about the concept of organisations.
        headers |= {"org": organisation}

    if msg:
        # We use metadata of the message to determine the mime type.
        # If the message contains an organisation, we prefer that as
        # the target instead of the queue_suffix.
        if "scan_spec" in msg:
            spec = msg["scan_spec"]
            organisation = spec["scan_tag"]["organisation"]["name"]
            headers |= {"org": organisation}
        elif "scan_tag" in msg:
            tag = msg["scan_tag"]
            organisation = tag["organisation"]["name"]
            headers |= {"org": organisation}

    if rk:
        # TODO: Implement tag extraction from routing_key.
        for q in ["os2ds_conversions", "os2ds_handles", "os2ds_representations"]:
            if q in rk:
                headers |= {}

    return dict(headers=headers)


def get_exchange(stage=None, queue_suffix=None, msg=None, rk=None):
    """Gets the appropriate exchange for dispatching a specific message (msg).
      This selection is based on the message (msg), routing_key (rk), stage, etc."""

    if rk:
        for q in ["os2ds_conversions", "os2ds_handles", "os2ds_representations"]:
            if q in rk:
                return "os2ds_root_conversions"
    return ""


def get_queues(qs, suffix=None):
    """Gets and formats the correct read queues for a module with an optional suffix."""
    return [f"{q}_{suffix}"
            if "os2ds_conversions" in q else q
            for q in qs] if suffix else qs
