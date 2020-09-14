from os import getpid

from prometheus_client import start_http_server

from ...utils.metadata import guess_responsible_party
from ..model.core import Handle, SourceManager
from . import messages
from .utilities import (notify_ready, PikaPipelineRunner, notify_stopping,
        prometheus_summary, make_common_argument_parser,
        make_sourcemanager_configuration_block)


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
    outputs.add_argument(
            "--problems",
            metavar="NAME",
            help="the name of the AMQP queue to which problems should be"
                    + " written",
            default="os2ds_problems")

    args = parser.parse_args()

    if args.enable_metrics:
        start_http_server(args.prometheus_port)


    class TaggerRunner(PikaPipelineRunner):
        @prometheus_summary(
                "os2datascanner_pipeline_tagger", "Metadata extractions")
        def handle_message(self, body, *, channel=None):
            if args.debug:
                print(channel, body)
            return message_received_raw(body,
                    channel, source_manager, args.metadata, args.problems)

    with SourceManager(width=args.width) as source_manager:
        with TaggerRunner(
                read=[args.handles],
                write=[args.metadata, args.problems],
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
