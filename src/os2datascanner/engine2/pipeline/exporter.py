from . import messages


READS_QUEUES = ("os2ds_matches", "os2ds_metadata", "os2ds_problems",)
WRITES_QUEUES = ("os2ds_results",)
PROMETHEUS_DESCRIPTION = "Messages exported"
PREFETCH_COUNT = 8


def censor_outgoing_message(message):
    """Censors a message before sending it to the outside world."""
    if isinstance(message, messages.MetadataMessage):
        return message._replace(handle=message.handle.censor())
    elif isinstance(message, messages.MatchesMessage):
        return message._replace(
                handle=message.handle.censor(),
                scan_spec=censor_outgoing_message(message.scan_spec))
    elif isinstance(message, messages.ProblemMessage):
        return message._replace(
                handle=message.handle.censor() if message.handle else None,
                source=message.source.censor() if message.source else None)
    else:
        return message


def message_received_raw(body, channel, source_manager):
    body["origin"] = channel

    message = None
    if "metadata" in body:
        message = messages.MetadataMessage.from_json_object(body)
    elif "matched" in body:
        message = messages.MatchesMessage.from_json_object(body)
    elif "message" in body:
        message = messages.ProblemMessage.from_json_object(body)
    # Old-style problem messages are now ignored

    if message:
        result_body = censor_outgoing_message(message).to_json_object()
        result_body["origin"] = channel

        yield ("os2ds_results", result_body)


if __name__ == "__main__":
    from .run_stage import _compatibility_main  # noqa
    _compatibility_main("exporter")
