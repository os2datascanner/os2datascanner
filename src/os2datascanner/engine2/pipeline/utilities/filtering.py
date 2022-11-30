"""Utilities for filtering handles based on exclusion rules
and type rules."""
import structlog

from ...model.core import Handle
from ...rules.rule import Rule

logger = structlog.get_logger(__name__)


def is_handle_relevant(handle: Handle, filter_rule: Rule) -> bool:
    """Checks whether a handle should be skipped based on the exclusion rule
    specified by a ScanSpecMessage and the global TypeRules."""
    h_p = handle.relative_path

    # Let everything pass if there is no filter_rule set.
    if filter_rule is None:
        return True

    # Apply the rule to the relative path of the handle.
    try:
        conclusion, _ = filter_rule.try_match(lambda t: h_p)
        return not conclusion
    except KeyError as error:
        exception_message = f"Filtering error. {type(error).__name__}: "
        exception_message += ", ".join([str(a) for a in error.args])

        logger.warning(exception_message)
        return True
