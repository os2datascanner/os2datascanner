import logging
from ..conversions.types import decode_dict
from . import messages
from .. import settings

logger = logging.getLogger(__name__)

READS_QUEUES = ("os2ds_representations",)
WRITES_QUEUES = (
    "os2ds_handles",
    "os2ds_matches",
    "os2ds_checkups",
    "os2ds_conversions",)
PROMETHEUS_DESCRIPTION = "Representations examined"
PREFETCH_COUNT = 8


def message_received_raw(body, channel, source_manager):  # noqa: CCR001,E501 too high cognitive complexity
    message = messages.RepresentationMessage.from_json_object(body)
    representations = decode_dict(message.representations)
    rule = message.progress.rule
    logger.debug(f"{message.handle} with rules [{rule.presentation}] "
                 f"and representation [{list(representations.keys())}]")

    try:
        # Keep executing rules for as long as we can with the representations
        # we have
        conclusion, new_matches = rule.try_match(
                representations,
                obj_limit=max(1, settings.pipeline["matcher"]["obj_limit"]))
    except Exception as e:
        exception_message = "Matching error"
        exception_message += ". {0}: ".format(type(e).__name__)
        exception_message += ", ".join([str(a) for a in e.args])
        logger.warning(exception_message)
        for problems_q in ("os2ds_problems", "os2ds_checkups",):
            yield (problems_q, messages.ProblemMessage(
                    scan_tag=message.scan_spec.scan_tag,
                    source=None, handle=message.handle,
                    message=exception_message).to_json_object())
        return

    final_matches = message.progress.matches + [
            messages.MatchFragment(rule, matches or None)
            for rule, matches in new_matches]

    if isinstance(conclusion, bool):
        # We've come to a conclusion!

        logger.info(
                f"{message.handle} done."
                f" Matched status: {conclusion}")

        for matches_q in ("os2ds_matches", "os2ds_checkups",):
            yield (matches_q,
                   messages.MatchesMessage(
                       message.scan_spec, message.handle,
                       matched=conclusion,
                       matches=final_matches).to_json_object())

        # Only trigger metadata scanning if the match succeeded
        if conclusion:
            yield ("os2ds_handles",
                   messages.HandleMessage(
                            message.scan_spec.scan_tag,
                            message.handle).to_json_object())
    else:
        new_rep = conclusion.split()[0].operates_on
        # We need a new representation to continue
        logger.debug(
                f"{message.handle} needs"
                f" new representation: [{new_rep}].")
        yield ("os2ds_conversions",
               messages.ConversionMessage(
                            message.scan_spec, message.handle,
                            message.progress._replace(
                                    rule=conclusion,
                                    matches=final_matches)).to_json_object())


if __name__ == "__main__":
    from .run_stage import _compatibility_main  # noqa
    _compatibility_main("matcher")
