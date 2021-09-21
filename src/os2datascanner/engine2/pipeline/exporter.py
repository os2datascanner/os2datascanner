import json
import argparse

from ..model.core import (Handle,
        Source, UnknownSchemeError, DeserialisationError)
from . import messages


READS_QUEUES = ("os2ds_matches", "os2ds_metadata", "os2ds_problems",)
WRITES_QUEUES = ("os2ds_results",)
PROMETHEUS_DESCRIPTION = "Messages exported"
PREFETCH_COUNT = 8


def message_received_raw(body, channel, source_manager):
    source_manager = None
    body["origin"] = channel

    message = None
    if "metadata" in body:
        message = messages.MetadataMessage.from_json_object(body)
        # MetadataMessages carry a scan tag rather than a complete scan spec,
        # so all we need to censor is the handle
        message = message._replace(handle=message.handle.censor())
    elif "matched" in body:
        message = messages.MatchesMessage.from_json_object(body)
        # Censor both the scan spec and the object handle
        censored_scan_spec = message.scan_spec._replace(
                source=message.scan_spec.source.censor())
        message = message._replace(
                handle=message.handle.censor(),
                scan_spec=censored_scan_spec)
    elif "message" in body:
        message = messages.ProblemMessage.from_json_object(body)
        message = message._replace(
                handle=message.handle.censor() if message.handle else None,
                source=message.source.censor() if message.source else None)
    # Old-style problem messages are now ignored

    if message:
        result_body = message.to_json_object()
        result_body["origin"] = channel

        yield ("os2ds_results", result_body)


if __name__ == "__main__":
    from .run_stage import _compatibility_main  # noqa
    _compatibility_main("exporter")
