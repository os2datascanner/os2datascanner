from os import getpid
import json
import argparse

from prometheus_client import start_http_server

from ..model.core import (Handle,
        Source, UnknownSchemeError, DeserialisationError)
from . import messages
from .utilities import (notify_ready, PikaPipelineRunner, notify_stopping,
        prometheus_summary, make_common_argument_parser)


def message_received_raw(body, channel, dump, results_q):
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

        # For debugging purposes
        if dump:
            print(json.dumps(result_body, indent=True))
            dump.write(json.dumps(result_body) + "\n")
            dump.flush()

        yield (results_q, result_body)


def main():
    parser = make_common_argument_parser()
    parser.description = ("Consume problems, metadata and matches, and convert"
                          + " them into forms suitable for the outside world.")

    inputs = parser.add_argument_group("inputs")
    inputs.add_argument(
            "--matches",
            metavar="NAME",
            help="the name of the AMQP queue from which matches should be"
                    " read",
            default="os2ds_matches")
    inputs.add_argument(
            "--problems",
            metavar="NAME",
            help="the name of the AMQP queue from which problems should be"
                    " read",
            default="os2ds_problems")
    inputs.add_argument(
            "--metadata",
            metavar="NAME",
            help="the name of the AMQP queue from which metadata should be"
                    " read",
            default="os2ds_metadata")

    outputs = parser.add_argument_group("outputs")
    outputs.add_argument(
            "--results",
            metavar="NAME",
            help="the name of the AMQP queue to which filtered result objects"
                    " should be written",
            default="os2ds_results")
    outputs.add_argument(
            "--dump",
            metavar="PATH",
            help="the name of a JSON Lines file to which filtered result"
                    "objects should also be appended",
            type=argparse.FileType(mode="at"),
            default=None)

    args = parser.parse_args()

    if args.enable_metrics:
        start_http_server(args.prometheus_port)


    class ExporterRunner(PikaPipelineRunner):
        @prometheus_summary(
                "os2datascanner_pipeline_exporter", "Messages exported")
        def handle_message(self, body, *, channel=None):
            if args.debug:
                print(channel, body)
            return message_received_raw(body, channel, args.dump, args.results)

    with ExporterRunner(
            read=[args.matches, args.metadata, args.problems],
            write=[args.results],
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
