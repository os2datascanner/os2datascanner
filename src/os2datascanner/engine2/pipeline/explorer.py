from ..model.core import Source, UnknownSchemeError, DeserialisationError
from . import messages

import structlog


logger = structlog.get_logger(__name__)


READS_QUEUES = ("os2ds_scan_specs",)
WRITES_QUEUES = (
        "os2ds_conversions", "os2ds_problems", "os2ds_status",
        "os2ds_scan_specs",)
PROMETHEUS_DESCRIPTION = "Sources explored"
# An individual exploration task is typically the longest kind of task, so we
# want to do as little prefetching as possible here. (If we're doing an
# agonisingly slow web scan, we don't want to hog scan specs we're not ready
# to use yet!)
PREFETCH_COUNT = 1


def message_received_raw(body, channel, source_manager):  # noqa
    try:
        scan_tag = messages.ScanTagFragment.from_json_object(body["scan_tag"])
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
        yield ("os2ds_problems", messages.ProblemMessage(
                scan_tag=scan_tag, source=None, handle=None,
                message=("Unknown scheme '{0}'".format(
                        ex.args[0]))).to_json_object())
        return
    except (KeyError, DeserialisationError):
        yield ("os2ds_problems", messages.ProblemMessage(
                scan_tag=scan_tag, source=None, handle=None,
                message="Malformed input").to_json_object())
        return

    handle_count = 0
    source_count = None
    exception_message = ""
    try:
        for handle in scan_spec.source.handles(source_manager):
            if not scan_spec.source.yields_independent_sources:
                if isinstance(handle, tuple) and handle[1]:
                    # This Handle threw an exception during exploration.
                    # Send a problem message, so the user can be notified.
                    handle_object, error = handle
                    exception_message = "Exploration error. {0}: ".format(type(error).__name__)
                    exception_message += ", ".join([str(a) for a in error.args])
                    problem_message = messages.ProblemMessage(
                        scan_tag=scan_tag, source=scan_spec.source, handle=handle_object,
                        message=exception_message)
                    yield ("os2ds_problems", problem_message.to_json_object())
                    logger.info(f"Sent problem message for handle: {handle_object}.")
                else:
                    # This Handle is just a normal reference to a scannable object.
                    # Send it on to be processed
                    yield ("os2ds_conversions",
                           messages.ConversionMessage(
                                scan_spec, handle, progress).to_json_object())
                    handle_count += 1
            else:
                # This Handle is a thin wrapper around an independent Source.
                # Construct that Source and enqueue it for further exploration
                new_source = Source.from_handle(handle)
                yield ("os2ds_scan_specs", scan_spec._replace(
                        source=new_source).to_json_object())
                source_count = (source_count or 0) + 1
        logger.info(
                "Finished exploration successfully",
                handle_count=handle_count, source_count=source_count,
                scan_tag=scan_tag)
    except Exception as e:
        exception_message = "Exploration error. {0}: ".format(type(e).__name__)
        exception_message += ", ".join([str(a) for a in e.args])
        problem_message = messages.ProblemMessage(
            scan_tag=scan_tag, source=scan_spec.source, handle=None,
            message=exception_message)
        yield ("os2ds_problems", problem_message.to_json_object())
        logger.warning(
                "Finished exploration unsuccessfully",
                handle_count=handle_count, source_count=source_count,
                scan_tag=scan_tag, exc_info=e)
    finally:
        yield ("os2ds_status", messages.StatusMessage(
                scan_tag=scan_tag,
                total_objects=handle_count, new_sources=source_count,
                message=exception_message,
                status_is_error=exception_message != "").to_json_object())


if __name__ == "__main__":
    from .run_stage import _compatibility_main  # noqa
    _compatibility_main("explorer")
