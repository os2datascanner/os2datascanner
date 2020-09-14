from os import getpid

from prometheus_client import start_http_server

from ..rules.rule import Rule
from ..model.core import Source, Handle, SourceManager
from ..conversions import convert
from ..conversions.types import OutputType, encode_dict
from . import messages
from .utilities import (notify_ready, PikaPipelineRunner, notify_stopping,
        prometheus_summary, make_common_argument_parser,
        make_sourcemanager_configuration_block)


def message_received_raw(body,
        channel, source_manager, representations_q, sources_q, problems_q):
    conversion = messages.ConversionMessage.from_json_object(body)
    configuration = conversion.scan_spec.configuration
    head, _, _ = conversion.progress.rule.split()
    required = head.operates_on

    try:
        resource = conversion.handle.follow(source_manager)

        representation = None
        if (required == OutputType.Text
                and "skip_mime_types" in configuration):
            mime_type = resource.compute_type()
            for mt in configuration["skip_mime_types"]:
                if mt.endswith("*") and mime_type.startswith(mt[:-1]):
                    break
                elif mime_type == mt:
                    break
            else:
                representation = convert(resource, OutputType.Text)
        else:
            representation = convert(resource, required)

        if representation and representation.parent:
            # If the conversion also produced other values at the same
            # time, then include all of those as well; they might also be
            # useful for the rule engine
            dv = {k.value: v.value
                    for k, v in representation.parent.items()
                    if isinstance(k, OutputType)}
        else:
            dv = {required.value: representation.value
                    if representation else None}

        yield (representations_q,
                messages.RepresentationMessage(
                        conversion.scan_spec, conversion.handle,
                        conversion.progress, encode_dict(dv)).to_json_object())
    except KeyError:
        # If we have a conversion we don't support, then check if the current
        # handle can be reinterpreted as a Source; if it can, then try again
        # with that
        derived_source = Source.from_handle(conversion.handle, source_manager)
        if derived_source:
            # Copy almost all of the existing scan spec, but note the progress
            # of rule execution and replace the source
            new_scan_spec = conversion.scan_spec._replace(
                    source=derived_source, progress=conversion.progress)
            yield (sources_q, new_scan_spec.to_json_object())
        else:
            # If we can't recurse any deeper, then produce an empty conversion
            # so that the matcher stage has something to work with
            # (XXX: is this always the right approach?)
            yield (representations_q,
                    messages.RepresentationMessage(
                            conversion.scan_spec, conversion.handle,
                            conversion.progress, {
                                required.value: None
                            }).to_json_object())
    except Exception as e:
        exception_message = ", ".join([str(a) for a in e.args])
        yield (problems_q, messages.ProblemMessage(
                scan_tag=conversion.scan_spec.scan_tag,
                source=None, handle=conversion.handle,
                message="Processing error: {0}".format(
                        exception_message)).to_json_object())


def main():
    parser = make_common_argument_parser()
    parser.description = ("Consume conversions and generate " +
            "representations and fresh sources.")

    inputs = parser.add_argument_group("inputs")
    inputs.add_argument(
            "--conversions",
            metavar="NAME",
            help="the name of the AMQP queue from which conversions"
                    + " should be read",
            default="os2ds_conversions")

    make_sourcemanager_configuration_block(parser)

    outputs = parser.add_argument_group("outputs")
    outputs.add_argument(
            "--representations",
            metavar="NAME",
            help="the name of the AMQP queue to which representations"
                    + " should be written",
            default="os2ds_representations")
    outputs.add_argument(
            "--sources",
            metavar="NAME",
            help="the name of the AMQP queue to which scan specifications"
                    + " should be written",
            default="os2ds_scan_specs")
    outputs.add_argument(
            "--problems",
            metavar="NAME",
            help="the name of the AMQP queue to which problems should be"
                    + " written",
            default="os2ds_problems")

    args = parser.parse_args()

    if args.enable_metrics:
        start_http_server(args.prometheus_port)


    class ProcessorRunner(PikaPipelineRunner):
        @prometheus_summary("os2datascanner_pipeline_processor",
                "Representations generated")
        def handle_message(self, body, *, channel=None):
            if args.debug:
                print(channel, body)
            return message_received_raw(body, channel, source_manager,
                    args.representations, args.sources, args.problems)

    with SourceManager(width=args.width) as source_manager:
        with ProcessorRunner(
                read=[args.conversions],
                write=[args.sources, args.representations, args.problems],
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
