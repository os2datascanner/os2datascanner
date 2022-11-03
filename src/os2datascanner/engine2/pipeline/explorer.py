from .. import settings
from ..model.core import Source, UnknownSchemeError, DeserialisationError
from ..utilities.backoff import TimeoutRetrier
from . import messages
from .utilities.filtering import is_handle_relevant

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


def process_exploration_error(scan_spec, handle_candidate, ex):
    exception_message = (
            f"Exploration error. {type(ex).__name__}: "
            + ", ".join(str(a) for a in ex.args))
    problem_message = messages.ProblemMessage(
            scan_tag=scan_spec.scan_tag, source=scan_spec.source,
            handle=handle_candidate, message=exception_message)
    yield ("os2ds_problems", problem_message.to_json_object())
    logger.info(
            "found problem",
            scan_tag=scan_spec.scan_tag, handle=handle_candidate)


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

    # Update the configuration of the source manager.
    # Yes, this is dreaded mutable state... Just don't go change it
    # somewhere else.
    source_manager.configuration = scan_spec.configuration

    it = scan_spec.source.handles(source_manager)

    tr = TimeoutRetrier(
            seconds=settings.pipeline["op_timeout"],
            max_tries=settings.pipeline["op_tries"])

    log = logger.bind(scan_tag=scan_tag)

    try:
        while (handle := tr.run(next, it)):
            if isinstance(handle, tuple) and handle[1]:
                # We were able to construct a Handle for something that
                # exists, but then something unexpected (that we can tie to
                # that specific Handle) went wrong. Send a problem message
                yield from process_exploration_error(scan_spec, *handle)
            elif not scan_spec.source.yields_independent_sources:
                # This Handle is just a normal reference to a scannable object.
                # Send it on to be processed
                yield ("os2ds_conversions",
                       messages.ConversionMessage(
                            scan_spec, handle, progress).to_json_object())
                handle_count += 1
            else:
                # Check if the handle should be excluded.
                if is_handle_relevant(handle, scan_spec.filter_rule):
                    # This Handle is a thin wrapper around an independent Source.
                    # Construct that Source and enqueue it for further exploration
                    new_source = Source.from_handle(handle)
                    yield ("os2ds_scan_specs", scan_spec._replace(
                        source=new_source).to_json_object())
                    source_count = (source_count or 0) + 1
                else:
                    log.info("handle excluded", handle=handle)

        log.warning("stopped unexpectedly")
    except StopIteration:
        # Exploration is complete
        log.info(
                "finished",
                handle_count=handle_count, source_count=source_count)
    except Exception as e:
        exception_message = "Exploration error. {0}: ".format(type(e).__name__)
        exception_message += ", ".join([str(a) for a in e.args])
        problem_message = messages.ProblemMessage(
            scan_tag=scan_tag, source=scan_spec.source, handle=None,
            message=exception_message)
        yield ("os2ds_problems", problem_message.to_json_object())
        log.warning(
                "finished unsuccessfully",
                handle_count=handle_count, source_count=source_count,
                exc_info=e)
    finally:
        if hasattr(it, "close"):
            it.close()
        yield ("os2ds_status", messages.StatusMessage(
                scan_tag=scan_tag,
                total_objects=handle_count, new_sources=source_count,
                message=exception_message,
                status_is_error=exception_message != "").to_json_object())


if __name__ == "__main__":
    from .run_stage import _compatibility_main  # noqa
    _compatibility_main("explorer")
