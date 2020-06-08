from typing import Sequence, NamedTuple

from ..model.core import Handle, Source
from ..rules.rule import Rule, SimpleRule, Sensitivity


class MatchFragment(NamedTuple):
    rule: SimpleRule
    matches: Sequence[dict]

    @classmethod
    def from_json_object(cls, obj):
        return MatchFragment(
                rule=Rule.from_json_object(obj["rule"]),
                matches=obj["matches"])


class ProgressFragment(NamedTuple):
    rule: Rule
    matches: Sequence[MatchFragment]

    @classmethod
    def from_json_object(cls, obj):
        return ProgressFragment(
                rule=Rule.from_json_object(obj["rule"]),
                matches=[MatchFragment.from_json_object(mf)
                        for mf in obj["matches"]])


class ScanSpecMessage(NamedTuple):
    scan_tag: object
    source: Source
    rule: Rule
    configuration: dict
    progress: ProgressFragment

    @classmethod
    def from_json_object(cls, obj):
        progress_fragment = obj.get("progress")
        return ScanSpecMessage(
                scan_tag=obj["scan_tag"],
                source=Source.from_json_object(obj["source"]),
                rule=Rule.from_json_object(obj["rule"]),
                configuration=obj.get("configuration"),
                progress=ProgressFragment.from_json_object(progress_fragment)
                        if progress_fragment else None)


class ConversionMessage(NamedTuple):
    scan_spec: ScanSpecMessage
    handle: Handle
    progress: ProgressFragment

    @classmethod
    def from_json_object(cls, obj):
        return ConversionMessage(
                scan_spec=ScanSpecMessage.from_json_object(obj["scan_spec"]),
                handle=Handle.from_json_object(obj["handle"]),
                progress=ProgressFragment.from_json_object(obj["progress"]))


class RepresentationMessage(NamedTuple):
    scan_spec: ScanSpecMessage
    handle: Handle
    progress: ProgressFragment
    representations: dict

    @classmethod
    def from_json_object(cls, obj):
        return RepresentationMessage(
                scan_spec=ScanSpecMessage.from_json_object(obj["scan_spec"]),
                handle=Handle.from_json_object(obj["handle"]),
                progress=ProgressFragment.from_json_object(obj["progress"]),
                representations=obj["representations"])


class HandleMessage(NamedTuple):
    scan_tag: object
    handle: Handle

    @classmethod
    def from_json_object(cls, obj):
        return HandleMessage(
                scan_tag=obj["scan_tag"],
                handle=Handle.from_json_object(obj["handle"]))


class MetadataMessage(NamedTuple):
    scan_tag: object
    handle: Handle
    metadata: dict

    @classmethod
    def from_json_object(cls, obj):
        return MetadataMessage(
                scan_tag=obj["scan_tag"],
                handle=Handle.from_json_object(obj["handle"]),
                metadata=obj["metadata"])


class MatchesMessage(NamedTuple):
    scan_spec: ScanSpecMessage
    handle: Handle
    matched: bool
    matches: Sequence[MatchFragment]

    @property
    def sensitivity(self):
        """Computes the overall sensitivity of the matches contained in this
        message (i.e., the highest sensitivity of any submatch), or None if
        there are no matches."""
        if not self.matches:
            return None
        else:

            def _cms(fragment):
                """Computes the sensitivity of a set of results returned by a
                rule, returning (in order of preference) the highest
                sensitivity (lower than that of the rule) associated with a
                match, the sensitivity of the rule, or 0."""
                rule_sensitivity = fragment.rule.sensitivity

                max_sub = None
                if (rule_sensitivity is not None
                        and fragment.matches is not None):
                    max_sub = None
                    for match_dict in fragment.matches:
                        if "sensitivity" in match_dict:
                            sub = match_dict["sensitivity"]
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
            return Sensitivity(max([_cms(frag) for frag in self.matches]))

    @staticmethod
    def from_json_object(obj):
        return MatchesMessage(
                scan_spec=ScanSpecMessage.from_json_object(obj["scan_spec"]),
                handle=Handle.from_json_object(obj["handle"]),
                matched=obj["matched"],
                matches=[MatchFragment.from_json_object(mf)
                        for mf in obj["matches"]])
