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


def explore(sm, msg):
    for channel, message in explorer_handler(msg, "ss", sm, "co", "pr", None):
        if channel == "co":
            yield from process(sm, message)
        elif channel in ('pr',):
            yield channel, message


def process(sm, msg):
    for channel, message in processor_handler(msg,
            "co", sm, "re", "ss", ["pr"]):
        if channel == "re":
            yield from match(sm, message)
        elif channel == "ss":
            yield from explore(sm, message)
        elif channel in ('pr',):
            yield channel, message


def match(sm, msg):
    for channel, message in matcher_handler(msg, "re", ["ma"], "me", "co"):
        if channel == "me":
            yield from tag(sm, message)
        elif channel == "co":
            yield from process(sm, message)
        elif channel in ('ma',):
            yield channel, message


def tag(sm, msg):
    yield from tagger_handler(msg, "ha", sm, "me", "pr")


def message_received_raw(body, channel,
        source_manager, matches_qs, metadata_q, problems_qs, status_q):
    try:
        for channel, message in process(source_manager, body):
            if channel == "ma":
                for matches_q in matches_qs:
                    yield (matches_q, message)
            elif channel == "me":
                yield (metadata_q, message)
            elif channel == "pr":
                for problems_q in problems_qs:
                    yield (problems_q, message)
    finally:
        if status_q:
            message = messages.ConversionMessage.from_json_object(body)
            object_size = 0
            object_type = "application/octet-stream"
            try:
                resource = message.handle.follow(source_manager)
                object_size = resource.get_size().value
                object_type = resource.compute_type()
            except Exception:
                pass
            yield (status_q, messages.StatusMessage(
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
            return message_received_raw(body, channel, source_manager,
                    ["os2ds_matches", "os2ds_checkups"], "os2ds_metadata",
                    ["os2ds_problems", "os2ds_checkups"], "os2ds_status")

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
