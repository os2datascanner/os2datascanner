from os import getpid

from prometheus_client import start_http_server

from ..model.core import SourceManager
from .utilities.args import (AppendReplaceAction, make_common_argument_parser,
        make_sourcemanager_configuration_block)
from .utilities.pika import PikaPipelineRunner
from .utilities.systemd import notify_ready, notify_stopping
from .utilities.prometheus import prometheus_summary
from .explorer import message_received_raw as explorer_handler
from .processor import message_received_raw as processor_handler
from .matcher import message_received_raw as matcher_handler
from .tagger import message_received_raw as tagger_handler
from . import messages


__reads_queues__ = ("os2ds_conversions",)
__writes_queues__ = ("os2ds_matches", "os2ds_checkups", "os2ds_problems",
        "os2ds_metadata", "os2ds_status",)


def explore(sm, msg):
    for channel, message in explorer_handler(msg, "os2ds_scan_specs", sm):
        if channel == "os2ds_conversions":
            yield from process(sm, message)
        elif channel in ("os2ds_problems",):
            yield channel, message


def process(sm, msg):
    for channel, message in processor_handler(msg, "os2ds_conversions", sm):
        if channel == "os2ds_representations":
            yield from match(sm, message)
        elif channel == "os2ds_scan_specs":
            yield from explore(sm, message)
        elif channel in ("os2ds_problems",):
            yield channel, message


def match(sm, msg):
    for channel, message in matcher_handler(msg, "os2ds_representations", sm):
        if channel == "os2ds_handles":
            yield from tag(sm, message)
        elif channel == "os2ds_conversions":
            yield from process(sm, message)
        elif channel in ("os2ds_matches",):
            yield channel, message


def tag(sm, msg):
    yield from tagger_handler(msg, "os2ds_handles", sm)


def message_received_raw(body, channel, source_manager):
    try:
        for channel, message in process(source_manager, body):
            if channel == "os2ds_matches":
                for matches_q in ("os2ds_matches", "os2ds_checkups",):
                    yield (matches_q, message)
            elif channel == "os2ds_metadata":
                yield ("os2ds_metadata", message)
            elif channel == "os2ds_problems":
                for problems_q in ("os2ds_problems", "os2ds_checkups",):
                    yield (problems_q, message)
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
                object_size=object_size,
                object_type=object_type).to_json_object())


def main():
    parser = make_common_argument_parser()
    parser.description = (
            "Consume and fully execute conversions, and generate matches and"
            " metadata messages.")

    make_sourcemanager_configuration_block(parser)

    args = parser.parse_args()

    if args.enable_metrics:
        start_http_server(args.prometheus_port)

    class ProcessorRunner(PikaPipelineRunner):
        @prometheus_summary("os2datascanner_pipeline_worker",
                "Objects handled")
        def handle_message(self, body, *, channel=None):
            if args.debug:
                print(channel, body)
            return message_received_raw(body, channel, source_manager)

    with SourceManager(width=args.width) as source_manager:
        with ProcessorRunner(
                read=["os2ds_conversions"],
                write=["os2ds_matches", "os2ds_checkups", "os2ds_problems",
                        "os2ds_metadata", "os2ds_status"],
                heartbeat=6000) as runner:
            try:
                print("Start")
                notify_ready()
                runner.run_consumer()
            finally:
                print("Stop")
                notify_stopping()

if __name__ == "__main__":
    main()
