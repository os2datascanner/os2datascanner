import logging
from urllib.error import HTTPError
from .. import settings
from ..model.core import Source
from ..utilities.backoff import TimeoutRetrier
from ..conversions import convert
from ..conversions.types import OutputType, encode_dict
from . import messages

logger = logging.getLogger(__name__)

READS_QUEUES = ("os2ds_conversions",)
WRITES_QUEUES = (
    "os2ds_scan_specs",
    "os2ds_representations",
    "os2ds_problems",
    "os2ds_checkups",)
PROMETHEUS_DESCRIPTION = "Representations generated"
PREFETCH_COUNT = 8


def check(source_manager, handle):
    """
    Runs Resource.check() on the top-level Handle behind a given Handle.
    """

    # In most cases top-level is the >ultimate top-level<, for example a container of files. In
    # cases where the next "layer" up has yields_independent_sources set true, f.e. email
    # accounts, we stop traversing. Thus checking the email's existence and not the mail
    # account's.
    while handle.source.handle:
        if not handle.source.handle.source.yields_independent_sources:
            handle = handle.source.handle
        else:
            break

    # Resource.check() returns False if the object has been deleted, True if it
    # still exists, and raises an exception if something unexpected happened.
    # Instead of trying to interpret that exception, we should let it bubble up
    # and be converted into a ProblemMessage
    return handle.follow(source_manager).check()


def format_exception_message(ex: Exception, conversion: messages.ConversionMessage) -> str:
    '''Utility function for formating exception messages depending on the exception type.'''
    exception_message = "Processing error. {0}: ".format(type(ex).__name__)

    path = str(conversion.handle)

    if ex is HTTPError and ex.code == 400:
        # We have a special case for HTTP 400: Bad Request.
        exception_message += f"Found broken URL: {str(ex.url)} while scanning: {path}"
    else:
        # This just formats generic errors.
        exception_message += ", ".join([str(a) for a in ex.args])

    return exception_message


def message_received_raw(body, channel, source_manager, *, _check=True):  # noqa: CCR001,E501,C901
    conversion = messages.ConversionMessage.from_json_object(body)
    configuration = conversion.scan_spec.configuration
    head, _, _ = conversion.progress.rule.split()
    required = head.operates_on
    exception = None

    tr = TimeoutRetrier(
            seconds=settings.pipeline["op_timeout"],
            max_tries=settings.pipeline["op_tries"])

    try:
        if _check and not tr.run(check, source_manager, conversion.handle):
            # The resource is missing (and we're in a context where we care).
            # Generate a special problem message and stop the generator
            # immediately
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
                representation = tr.run(convert, resource, OutputType.Text)
        else:
            representation = tr.run(convert, resource, required)

        if representation and getattr(representation, "parent", None):
            # If the conversion also produced other values at the same
            # time, then include all of those as well; they might also be
            # useful for the rule engine
            dv = {k.value: v for k, v in representation.parent.items()
                  if isinstance(k, OutputType)}
        else:
            dv = {required.value: representation}

        logger.info(f"Required representation for {conversion.handle} is {required}")
        yield ("os2ds_representations",
               messages.RepresentationMessage(
                        conversion.scan_spec, conversion.handle,
                        conversion.progress, encode_dict(dv)).to_json_object())
    except KeyError:
        # If we have a conversion we don't support, then check if the current
        # handle can be reinterpreted as a Source; if it can, then try again
        # with that
        try:
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
            exception = e

    except Exception as e:
        exception = e

    if exception:
        exception_message = format_exception_message(exception, conversion)
        logger.warning(exception_message)

        for problems_q in ("os2ds_problems", "os2ds_checkups",):
            yield (problems_q, messages.ProblemMessage(
                    scan_tag=conversion.scan_spec.scan_tag,
                    source=None, handle=conversion.handle,
                    message=exception_message).to_json_object())


if __name__ == "__main__":
    from .run_stage import _compatibility_main  # noqa
    _compatibility_main("processor")
