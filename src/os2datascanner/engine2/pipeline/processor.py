import logging
from ..rules.rule import Rule
from ..model.core import Source, Handle, SourceManager
from ..conversions import convert
from ..conversions.types import OutputType, encode_dict
from . import messages

logger = logging.getLogger(__name__)

READS_QUEUES = ("os2ds_conversions",)
WRITES_QUEUES = ("os2ds_scan_specs", "os2ds_representations",
        "os2ds_problems", "os2ds_checkups",)
PROMETHEUS_DESCRIPTION = "Representations generated"


def check(source_manager, handle):
    """Runs Resource.check() on the ultimate top-level Handle behind a given
    Handle."""
    while handle.source.handle:
        handle = handle.source.handle
    try:
        return handle.follow(source_manager).check()
    except Exception as e:
        logger.warning("check of {0} failed: {1}".format(handle.presentation, e))
        return False


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

        if conversion.handle not in conversion.scan_spec.source:
            # handle point to a source outside the original scan_spec source, so
            # do nothing
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


if __name__ == "__main__":
    from .run_stage import _compatibility_main  # noqa
    _compatibility_main("processor")
