from os import getpid

from prometheus_client import start_http_server

from ..model.core import (Source, SourceManager, UnknownSchemeError,
        DeserialisationError)
from . import messages
from .utilities import (notify_ready, PikaPipelineRunner, notify_stopping,
        prometheus_summary, make_common_argument_parser,
        make_sourcemanager_configuration_block)


def message_received_raw(
        body, channel, source_manager, conversions_q, problems_q):
    try:
        scan_tag = body["scan_tag"]
    except KeyError:
        # Scan specifications with no scan tag are simply invalid and should be
        # dropped
        return

    try:
        scan_spec = messages.ScanSpecMessage.from_json_object(body)

        if scan_spec.progress:
            progress = scan_spec.progress
            scan_spec = scan_spec._replace(progress=None)
        else:
            progress = messages.ProgressFragment(
                    rule=scan_spec.rule, matches=[])
    except UnknownSchemeError as ex:
        yield (problems_q, messages.ProblemMessage(
                scan_tag=scan_tag, source=None, handle=None,
                message=("Unknown scheme '{0}'".format(
                        ex.args[0]))).to_json_object())
        return
    except (KeyError, DeserialisationError) as ex:
        yield (problems_q, messages.ProblemMessage(
                scan_tag=scan_tag, source=None, handle=None,
                message="Malformed input").to_json_object())
        return

    try:
        for handle in scan_spec.source.handles(source_manager):
            try:
                print(handle.censor())
            except NotImplementedError:
                # If a Handle doesn't implement censor(), then that indicates
                # that it doesn't know enough about its internal state to
                # censor itself -- just print its type
                print("(unprintable {0})".format(type(handle).__name__))
            yield (conversions_q,
                    messages.ConversionMessage(
                            scan_spec, handle, progress).to_json_object())
    except Exception as e:
        exception_message = ", ".join([str(a) for a in e.args])
        yield (problems_q, messages.ProblemMessage(
                scan_tag=scan_tag, source=scan_spec.source, handle=None,
                message="Exploration error: {0}".format(
                        exception_message)).to_json_object())


def main():
    parser = make_common_argument_parser()
    parser.description = "Consume sources and generate conversions."

    inputs = parser.add_argument_group("inputs")
    inputs.add_argument(
            "--sources",
            metavar="NAME",
            help="the name of the AMQP queue from which scan specifications"
                    + " should be read",
            default="os2ds_scan_specs")

    make_sourcemanager_configuration_block(parser)

    outputs = parser.add_argument_group("outputs")
    outputs.add_argument(
            "--conversions",
            metavar="NAME",
            help="the name of the AMQP queue to which conversions should be"
                    + " written",
            default="os2ds_conversions")
    outputs.add_argument(
            "--problems",
            metavar="NAME",
            help="the name of the AMQP queue to which problems should be"
                    + " written",
            default="os2ds_problems")

    args = parser.parse_args()

    if args.enable_metrics:
        start_http_server(args.prometheus_port)


    class ExplorerRunner(PikaPipelineRunner):
        @prometheus_summary(
                "os2datascanner_pipeline_explorer", "Sources explored")
        def handle_message(self, body, *, channel=None):
            if args.debug:
                print(channel, body)
            return message_received_raw(body, channel,
                    self.source_manager, args.conversions, args.problems)

    with SourceManager(width=args.width) as source_manager:
        with ExplorerRunner(
                read=[args.sources],
                write=[args.conversions, args.problems],
                source_manager=source_manager,
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
