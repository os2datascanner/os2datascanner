from typing import NamedTuple

from ..model.core import Handle
from ..rules.rule import Sensitivity


class MatchesMessage(NamedTuple):
    scan_spec: dict
    handle: Handle
    matched: bool
    matches: list

    @property
    def sensitivity(self):
        """Computes the overall sensitivity of the matches contained in this
        message (i.e., the highest sensitivity of any submatch), or None if
        there are no matches."""
        if not self.matches:
            return None
        else:

            def _cms(rule_result):
                """Computes the sensitivity of a set of results returned by a
                rule, returning (in order of preference) the highest
                sensitivity (lower than that of the rule) associated with a
                match, the sensitivity of the rule, or 0."""
                rule_sensitivity = None
                if "sensitivity" in rule_result["rule"]:
                    rule_sensitivity = rule_result["rule"]["sensitivity"]

                max_sub = None
                if (rule_sensitivity is not None
                        and rule_result["matches"] is not None):
                    max_sub = None
                    for match in rule_result["matches"]:
                        if "sensitivity" in match:
                            sub = match["sensitivity"]
                            if max_sub is None or sub > max_sub:
                                max_sub = sub
                if max_sub is not None:
                    # Matches can only have a lower sensitivity than their
                    # rule, never a higher one
                    return min(rule_sensitivity or 0, max_sub)
                elif rule_sensitivity is not None:
                    return rule_sensitivity
                else:
                    return 0
            return Sensitivity(
                    max([_cms(rule_result) for rule_result in self.matches]))

    @property
    def probability(self):
        """Computes the overall probability of the matches contained in this
        message (i.e., the highest probability of any submatch), or None if
        there are no matches."""
        if not self.matches:
            return None
        else:

            def _cmp(rule_result):
                """Computes the probability of a set of results returned by a
                rule, returning the highest probability associated with a
                match."""
                max_sub = None
                if rule_result["matches"] is not None:
                    max_sub = None
                    for match in rule_result["matches"]:
                        if "probability" in match:
                            sub = match["probability"]
                            if max_sub is None or sub > max_sub:
                                max_sub = sub
                if max_sub is not None:
                    return max_sub
                else:
                    return 0
        return max([_cmp(rule_result) for rule_result in self.matches])

    @staticmethod
    def from_json_object(obj):
        return MatchesMessage(
                scan_spec=obj["scan_spec"],
                handle=Handle.from_json_object(obj["handle"]),
                matched=obj["matched"],
                matches=obj["matches"])
