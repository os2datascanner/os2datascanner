from uuid import UUID
from typing import Optional, Sequence, NamedTuple
from datetime import datetime
import warnings

from os2datascanner.utils.system_utilities import parse_isoformat_timestamp
from ..model.core import Handle, Source
from ..rules.rule import Rule, SimpleRule, Sensitivity


def _deep_replace(self, **kwargs):
    """As NamedTuple._replace, but supports deeply nested field replacement
    using Django-like syntax ("tuple1__subtuple__field")."""
    p = self
    for name, value in kwargs.items():
        name = name.split("__")
        if len(name) > 1:
            head, tail = name[0], name[1:]
            fragment = getattr(p, head)
            p = p._replace(**{
                head: fragment._deep_replace(**{
                    "__".join(tail): value
                })
            })
        else:
            p = p._replace(**{name[0]: value})
    return p


class MatchFragment(NamedTuple):
    rule: SimpleRule
    matches: Optional[Sequence[dict]]

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

    _deep_replace = _deep_replace


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

    _deep_replace = _deep_replace


class ScannerFragment(NamedTuple):
    pk: int
    name: str

    def to_json_object(self):
        return {
            "pk": self.pk,
            "name": self.name
        }

    @classmethod
    def from_json_object(cls, obj):
        return ScannerFragment(pk=obj["pk"], name=obj["name"])

    _deep_replace = _deep_replace


class OrganisationFragment(NamedTuple):
    name: str
    uuid: Optional[UUID]

    def to_json_object(self):
        return {
            "name": self.name,
            "uuid": str(self.uuid) if self.uuid else None
        }

    @classmethod
    def from_json_object(cls, obj):
        try:
            return OrganisationFragment(
                    name=obj["name"], uuid=UUID(obj["uuid"]))
        except TypeError:
            # Organisation fragments created between versions 3.3.3 and 3.6.0
            # inclusive were just names
            return OrganisationFragment(name=obj, uuid=None)

    _deep_replace = _deep_replace


class ScanTagFragment(NamedTuple):
    time: datetime
    user: Optional[str]
    scanner: Optional[ScannerFragment]
    organisation: Optional[OrganisationFragment]
    destination: Optional[str] = "pipeline_collector"

    def to_json_object(self):
        return {
            "time": self.time.isoformat(),
            "user": self.user,
            "scanner": self.scanner.to_json_object() if self.scanner else None,
            "organisation": (self.organisation.to_json_object()
                             if self.organisation
                             else None),
            "destination": self.destination
        }

    @classmethod
    def from_json_object(cls, obj):
        try:
            return ScanTagFragment(
                    time=parse_isoformat_timestamp(obj["time"]),
                    user=obj["user"],  # can be None, must be present
                    scanner=ScannerFragment.from_json_object(obj["scanner"]),
                    organisation=OrganisationFragment.from_json_object(
                            obj["organisation"]))
        except KeyError:
            warnings.warn("trying to decode unrecognised scan tag object")
            time = obj.get("time")
            user = obj.get("user")
            scanner = obj.get("scanner")
            organisation = obj.get("organisation")
            return ScanTagFragment(
                    time=parse_isoformat_timestamp(time) if time else None,
                    user=user or None,
                    scanner=ScannerFragment.from_json_object(
                            scanner) if scanner else None,
                    organisation=OrganisationFragment.from_json_object(
                            organisation) if organisation else None)
        except TypeError:
            # Scan tags created between versions 3.0.0 and 3.3.2 inclusive were
            # just simple timestamps
            return ScanTagFragment(
                    time=parse_isoformat_timestamp(obj),
                    user=None, scanner=None, organisation=None)

    _deep_replace = _deep_replace


class ScanSpecMessage(NamedTuple):
    scan_tag: ScanTagFragment
    source: Source
    rule: Rule
    configuration: dict
    progress: ProgressFragment

    def to_json_object(self):
        return {
            "scan_tag": self.scan_tag.to_json_object(),
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
                scan_tag=ScanTagFragment.from_json_object(obj["scan_tag"]),
                source=Source.from_json_object(obj["source"]),
                rule=Rule.from_json_object(obj["rule"]),
                # The configuration dictionary was added fairly late to scan
                # specs, so not all clients will send it. Add an empty one if
                # necessary
                configuration=obj.get("configuration", {}),
                progress=(
                    ProgressFragment.from_json_object(progress_fragment)
                    if progress_fragment
                    else None))

    _deep_replace = _deep_replace


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

    _deep_replace = _deep_replace


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

    _deep_replace = _deep_replace


class HandleMessage(NamedTuple):
    scan_tag: ScanTagFragment
    handle: Handle

    def to_json_object(self):
        return {
            "scan_tag": self.scan_tag.to_json_object(),
            "handle": self.handle.to_json_object()
        }

    @classmethod
    def from_json_object(cls, obj):
        return HandleMessage(
                scan_tag=ScanTagFragment.from_json_object(obj["scan_tag"]),
                handle=Handle.from_json_object(obj["handle"]))

    _deep_replace = _deep_replace


class MetadataMessage(NamedTuple):
    scan_tag: ScanTagFragment
    handle: Handle
    metadata: dict

    def to_json_object(self):
        return {
            "scan_tag": self.scan_tag.to_json_object(),
            "handle": self.handle.to_json_object(),
            "metadata": self.metadata
        }

    @classmethod
    def from_json_object(cls, obj):
        return MetadataMessage(
                scan_tag=ScanTagFragment.from_json_object(obj["scan_tag"]),
                handle=Handle.from_json_object(obj["handle"]),
                metadata=obj["metadata"])

    _deep_replace = _deep_replace


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
                rule_sensitivity = (
                    fragment.rule.sensitivity.value
                    if fragment.rule.sensitivity
                    else None)

                max_sub = None
                if (rule_sensitivity is not None
                        and fragment.matches is not None):
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

    @property
    def probability(self):
        """Computes the overall probability of the matches contained in this
        message (i.e., the highest probability of any submatch), or None if
        there are no matches."""
        if not self.matches:
            return None
        else:

            def _cmp(fragment):
                """Computes the probability of a set of results returned by a
                rule, returning the highest probability associated with a
                match."""
                max_sub = None
                if fragment.matches is not None:
                    for match_dict in fragment.matches:
                        if "probability" in match_dict:
                            sub = match_dict["probability"]
                            if max_sub is None or sub > max_sub:
                                max_sub = sub
                if max_sub is not None:
                    return max_sub
                else:
                    return 0
        return max([_cmp(frag) for frag in self.matches])

    @staticmethod
    def from_json_object(obj):
        return MatchesMessage(
                scan_spec=ScanSpecMessage.from_json_object(obj["scan_spec"]),
                handle=Handle.from_json_object(obj["handle"]),
                matched=obj["matched"],
                matches=[MatchFragment.from_json_object(mf)
                         for mf in obj["matches"]])

    _deep_replace = _deep_replace


class ProblemMessage(NamedTuple):
    scan_tag: ScanTagFragment
    source: Optional[Source]
    handle: Optional[Handle]
    message: str
    missing: bool = False

    def to_json_object(self):
        return {
            "scan_tag": self.scan_tag.to_json_object(),
            "source": self.source.to_json_object() if self.source else None,
            "handle": self.handle.to_json_object() if self.handle else None,
            "message": self.message,
            "missing": self.missing
        }

    @staticmethod
    def from_json_object(obj):
        source = obj.get("source")
        handle = obj.get("handle")
        return ProblemMessage(
                scan_tag=ScanTagFragment.from_json_object(obj["scan_tag"]),
                source=Source.from_json_object(source) if source else None,
                handle=Handle.from_json_object(handle) if handle else None,
                message=obj["message"],
                missing=obj.get("missing", False))

    _deep_replace = _deep_replace


class StatusMessage(NamedTuple):
    scan_tag: ScanTagFragment
    message: str = ""
    status_is_error: bool = False

    # Emitted by (top-level) explorers
    total_objects: Optional[int] = None

    # Emitted by workers
    object_size: Optional[int] = None
    object_type: Optional[str] = None

    def to_json_object(self):
        return {
            "scan_tag": self.scan_tag.to_json_object(),
            "message": self.message,
            "status_is_error": self.status_is_error,

            "total_objects": self.total_objects,

            "object_size": self.object_size,
            "object_type": self.object_type
        }

    @staticmethod
    def from_json_object(obj):
        return StatusMessage(
                scan_tag=ScanTagFragment.from_json_object(obj["scan_tag"]),
                message=obj.get("message"),
                status_is_error=obj.get("status_is_error"),
                total_objects=obj.get("total_objects"),
                object_size=obj.get("object_size"),
                object_type=obj.get("object_type"))

    _deep_replace = _deep_replace


class CommandMessage(NamedTuple):
    """A CommandMessage is an order from the administration system. As they may
    modify the treatment of other messages, they should be processed as soon as
    possible, and so should be sent on a high-priority queue."""

    abort: Optional[ScanTagFragment]
    """If set, the scan tag of a scan that should no longer be processed by the
    pipeline. Pipeline components should acknowledge and silently ignore all
    messages carrying this tag.

    To avoid accumulating tags indefinitely, pipeline components should store
    them in a ring buffer of a reasonable size. (What "reasonable" means
    depends a bit on the installation and on how many concurrent scans it can
    be expected to perform.)"""

    log_level: Optional[int]
    """If set, the new logging level of the "os2datascanner" root logger."""

    def to_json_object(self):
        return {
            "abort": self.abort.to_json_object() if self.abort else None,
            "log_level": self.log_level
        }

    @staticmethod
    def from_json_object(obj):
        abort = obj.get("abort")
        return CommandMessage(
                abort=ScanTagFragment.from_json_object(abort)
                if abort else None,
                log_level=obj.get("log_level"))

    _deep_replace = _deep_replace
