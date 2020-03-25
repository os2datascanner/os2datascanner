from os import getpid

from ...utils.metadata import guess_responsible_party
from ...utils.prometheus import prometheus_session
from ..model.core import Handle, SourceManager, ResourceUnavailableError
from .utilities import (notify_ready, PikaPipelineRunner, notify_stopping,
        prometheus_summary, make_common_argument_parser,
        make_sourcemanager_configuration_block)


def message_received_raw(body, channel, source_manager, metadata_q):
    handle = Handle.from_json_object(body["handle"])

    try:
        yield (metadata_q, {
            "scan_tag": body["scan_tag"],
            "handle": body["handle"],
            "metadata": guess_responsible_party(handle, source_manager)
        })
    except ResourceUnavailableError as ex:
        pass


def main():
    parser = make_common_argument_parser()
    parser.description = "Consume handles and generate metadata."

    inputs = parser.add_argument_group("inputs")
    inputs.add_argument(
            "--handles",
            metavar="NAME",
            help="the name of the AMQP queue from which handles"
                    + " should be read",
            default="os2ds_handles")

    make_sourcemanager_configuration_block(parser)

    outputs = parser.add_argument_group("outputs")
    outputs.add_argument(
            "--metadata",
            metavar="NAME",
            help="the name of the AMQP queue to which metadata should be"
                    + " written",
            default="os2ds_metadata")

    args = parser.parse_args()

    class TaggerRunner(PikaPipelineRunner):
        @prometheus_summary(
                "os2datascanner_pipeline_tagger", "Metadata extractions")
        def handle_message(self, body, *, channel=None):
            if args.debug:
                print(channel, body)
            return message_received_raw(
                    body, channel, source_manager, args.metadata)

    with prometheus_session(
            str(getpid()),
            args.prometheus_dir,
            stage_type="tagger"):
        with SourceManager(width=args.width) as source_manager:
            with ProcessorRunner(
                    read=[args.handles],
                    write=[args.metadata],
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
