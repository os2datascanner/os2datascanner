from ..model.core import Handle, SourceManager
from . import messages


__reads_queues__ = ("os2ds_handles",)
__writes_queues__ = ("os2ds_metadata", "os2ds_problems",)


def message_received_raw(body, channel, source_manager):
    message = messages.HandleMessage.from_json_object(body)

    try:
        yield ("os2ds_metadata",
                messages.MetadataMessage(
                        message.scan_tag, message.handle,
                        message.handle.follow(source_manager).get_metadata()
                ).to_json_object())
    except Exception as e:
        exception_message = ", ".join([str(a) for a in e.args])
        yield ("os2ds_problems", messages.ProblemMessage(
                scan_tag=message.scan_tag,
                source=None, handle=message.handle,
                message="Metadata extraction error: {0}".format(
                        exception_message)).to_json_object())


if __name__ == "__main__":
    from .run_stage import _compatibility_main  # noqa
    _compatibility_main("tagger")
