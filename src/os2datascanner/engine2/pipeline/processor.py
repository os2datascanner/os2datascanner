from os import getpid

from prometheus_client import start_http_server

from ..rules.rule import Rule
from ..model.core import Source, Handle, SourceManager
from ..conversions import convert
from ..conversions.types import OutputType, encode_dict
from . import messages
from .utilities.args import (AppendReplaceAction, make_common_argument_parser,
        make_sourcemanager_configuration_block)
from .utilities.pika import PikaPipelineRunner
from .utilities.systemd import notify_ready, notify_stopping
from .utilities.prometheus import prometheus_summary


__reads_queues__ = ("os2ds_conversions",)
__writes_queues__ = ("os2ds_scan_specs", "os2ds_representations",
        "os2ds_problems", "os2ds_checkups",)


def check(source_manager, handle):
    """Runs Resource.check() on the ultimate top-level Handle behind a given
    Handle."""
    while handle.source.handle:
        handle = handle.source.handle
    return handle.follow(source_manager).check()


def message_received_raw(body, channel, source_manager):
    conversion = messages.ConversionMessage.from_json_object(body)
    configuration = conversion.scan_spec.configuration
    head, _, _ = conversion.progress.rule.split()
    required = head.operates_on

    try:
        if not check(source_manager, conversion.handle):
            # The resource is missing. Generate a special problem message and
            # stop the generator immediately
            for problems_q in ("os2ds_problems", "os2ds_checkups",):
                yield (problems_q, messages.ProblemMessage(
                        scan_tag=conversion.scan_spec.scan_tag,
                        source=None, handle=conversion.handle, missing=True,
                        message="Resource check failed").to_json_object())
            return

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

        yield ("os2ds_representations",
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
            yield ("os2ds_scan_specs", new_scan_spec.to_json_object())
        else:
            # If we can't recurse any deeper, then produce an empty conversion
            # so that the matcher stage has something to work with
            # (XXX: is this always the right approach?)
            yield ("os2ds_representations",
                    messages.RepresentationMessage(
                            conversion.scan_spec, conversion.handle,
                            conversion.progress, {
                                required.value: None
                            }).to_json_object())
    except Exception as e:
        exception_message = ", ".join([str(a) for a in e.args])
        for problems_q in ("os2ds_problems", "os2ds_checkups",):
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
            action=AppendReplaceAction,
            metavar="NAME",
            help="the names of the AMQP queues to which problems should be"
                    + " written",
            default=["os2ds_problems", "os2ds_checkups"])

    args = parser.parse_args()

    if args.enable_metrics:
        start_http_server(args.prometheus_port)


    class ProcessorRunner(PikaPipelineRunner):
        @prometheus_summary("os2datascanner_pipeline_processor",
                "Representations generated")
        def handle_message(self, body, *, channel=None):
            if args.debug:
                print(channel, body)
            return message_received_raw(body, channel, source_manager)

    with SourceManager(width=args.width) as source_manager:
        with ProcessorRunner(
                read=["os2ds_conversions"],
                write=["os2ds_scan_specs", "os2ds_representations",
                        "os2ds_problems", "os2ds_checkups"],
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
