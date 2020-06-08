from typing import Sequence, NamedTuple

from ..model.core import Handle, Source
from ..rules.rule import Rule, SimpleRule, Sensitivity


class MatchFragment(NamedTuple):
    rule: SimpleRule
    matches: Sequence[dict]

    def to_json_object(self):
        return {
            "rule": self.rule.to_json_object(),
            "matches": list(self.matches) if self.matches else None
        }

    @classmethod
    def from_json_object(cls, obj):
        return MatchFragment(
                rule=Rule.from_json_object(obj["rule"]),
                matches=obj["matches"])


class ProgressFragment(NamedTuple):
    rule: Rule
    matches: Sequence[MatchFragment]

    def to_json_object(self):
        return {
            "rule": self.rule.to_json_object(),
            "matches": list([m.to_json_object() for m in self.matches])
        }

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

    def to_json_object(self):
        return {
            "scan_tag": self.scan_tag,
            "source": self.source.to_json_object(),
            "rule": self.rule.to_json_object(),
            "configuration": self.configuration or {},
            "progress": (
                    self.progress.to_json_object() if self.progress else None)
        }

    @classmethod
    def from_json_object(cls, obj):
        # The progress fragment is only present when a scan spec is based on a
        # derived source and so already contains scan progress information
        progress_fragment = obj.get("progress")
        return ScanSpecMessage(
                scan_tag=obj["scan_tag"],
                source=Source.from_json_object(obj["source"]),
                rule=Rule.from_json_object(obj["rule"]),
                # The configuration dictionary was added fairly late to scan
                # specs, so not all clients will send it. Add an empty one if
                # necessary
                configuration=obj.get("configuration", {}),
                progress=ProgressFragment.from_json_object(progress_fragment)
                        if progress_fragment else None)


class ConversionMessage(NamedTuple):
    scan_spec: ScanSpecMessage
    handle: Handle
    progress: ProgressFragment

    def to_json_object(self):
        return {
            "scan_spec": self.scan_spec.to_json_object(),
            "handle": self.handle.to_json_object(),
            "progress": self.progress.to_json_object()
        }

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

    def to_json_object(self):
        return {
            "scan_spec": self.scan_spec.to_json_object(),
            "handle": self.handle.to_json_object(),
            "progress": self.progress.to_json_object(),
            "representations": self.representations
        }

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

    def to_json_object(self):
        return {
            "scan_tag": self.scan_tag,
            "handle": self.handle.to_json_object()
        }

    @classmethod
    def from_json_object(cls, obj):
        return HandleMessage(
                scan_tag=obj["scan_tag"],
                handle=Handle.from_json_object(obj["handle"]))


class MetadataMessage(NamedTuple):
    scan_tag: object
    handle: Handle
    metadata: dict

    def to_json_object(self):
        return {
            "scan_tag": self.scan_tag,
            "handle": self.handle.to_json_object(),
            "metadata": self.metadata
        }

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

    def to_json_object(self):
        return {
            "scan_spec": self.scan_spec.to_json_object(),
            "handle": self.handle.to_json_object(),
            "matched": self.matched,
            "matches": list([mf.to_json_object() for mf in self.matches])
        }

    @staticmethod
    def from_json_object(obj):
        return MatchesMessage(
                scan_spec=ScanSpecMessage.from_json_object(obj["scan_spec"]),
                handle=Handle.from_json_object(obj["handle"]),
                matched=obj["matched"],
                matches=[MatchFragment.from_json_object(mf)
                        for mf in obj["matches"]])
