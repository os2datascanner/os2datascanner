from os import getpid

from prometheus_client import start_http_server

from ...utils.metadata import guess_responsible_party
from ..model.core import Handle, SourceManager
from . import messages
from .utilities.args import (make_common_argument_parser,
        make_sourcemanager_configuration_block)
from .utilities.pika import PikaPipelineRunner
from .utilities.systemd import notify_ready, notify_stopping
from .utilities.prometheus import prometheus_summary


def message_received_raw(body,
        channel, source_manager, metadata_q, problems_q):
    message = messages.HandleMessage.from_json_object(body)

    try:
        yield (metadata_q,
                messages.MetadataMessage(
                        message.scan_tag, message.handle,
                        guess_responsible_party(
                                message.handle,
                                source_manager)).to_json_object())
    except Exception as e:
        exception_message = ", ".join([str(a) for a in e.args])
        yield (problems_q, messages.ProblemMessage(
                scan_tag=message.scan_tag,
                source=None, handle=message.handle,
                message="Metadata extraction error: {0}".format(
                        exception_message)).to_json_object())


def main():
    parser = make_common_argument_parser()
    parser.description = "Consume handles and generate metadata."

    make_sourcemanager_configuration_block(parser)


    args = parser.parse_args()

    if args.enable_metrics:
        start_http_server(args.prometheus_port)


    class TaggerRunner(PikaPipelineRunner):
        @prometheus_summary(
                "os2datascanner_pipeline_tagger", "Metadata extractions")
        def handle_message(self, body, *, channel=None):
            if args.debug:
                print(channel, body)
            return message_received_raw(body, channel,
                    source_manager, "os2ds_metadata", "os2ds_problems")

    with SourceManager(width=args.width) as source_manager:
        with TaggerRunner(
                read=["os2ds_handles"],
                write=["os2ds_metadata", "os2ds_problems"],
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
