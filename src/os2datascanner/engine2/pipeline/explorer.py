from ..model.core import (Source, SourceManager, UnknownSchemeError,
        DeserialisationError)
from . import messages


__reads_queues__ = ("os2ds_scan_specs",)
__writes_queues__ = ("os2ds_conversions", "os2ds_problems", "os2ds_status",)


def message_received_raw(body, channel, source_manager):
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
        yield ("os2ds_problems", messages.ProblemMessage(
                scan_tag=scan_tag, source=None, handle=None,
                message=("Unknown scheme '{0}'".format(
                        ex.args[0]))).to_json_object())
        return
    except (KeyError, DeserialisationError) as ex:
        yield ("os2ds_problems", messages.ProblemMessage(
                scan_tag=scan_tag, source=None, handle=None,
                message="Malformed input").to_json_object())
        return

    count = 0
    try:
        for handle in scan_spec.source.handles(source_manager):
            try:
                print(handle.censor())
            except NotImplementedError:
                # If a Handle doesn't implement censor(), then that indicates
                # that it doesn't know enough about its internal state to
                # censor itself -- just print its type
                print("(unprintable {0})".format(type(handle).__name__))
            count += 1
            yield ("os2ds_conversions",
                    messages.ConversionMessage(
                            scan_spec, handle, progress).to_json_object())
    except Exception as e:
        exception_message = ", ".join([str(a) for a in e.args])
        yield ("os2ds_problems", messages.ProblemMessage(
                scan_tag=scan_tag, source=scan_spec.source, handle=None,
                message="Exploration error: {0}".format(
                        exception_message)).to_json_object())
    finally:
        if "os2ds_status":
            yield ("os2ds_status", messages.StatusMessage(
                    scan_tag=scan_tag, total_objects=count).to_json_object())


if __name__ == "__main__":
    from .run_stage import _compatibility_main  # noqa
    _compatibility_main("explorer")
