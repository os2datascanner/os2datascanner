from typing import NamedTuple

from django.db import models
from django.contrib.postgres.fields import JSONField

from os2datascanner.engine2.model.core import Handle
from os2datascanner.engine2.rules.rule import Sensitivity


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
                sensitivity associated with a match, the sensitivity of the
                rule, or 0."""
                print(rule_result)
                max_sub = None
                if rule_result["matches"] is not None:
                    max_sub = None
                    for match in rule_result["matches"]:
                        if "sensitivity" in match:
                            sub = match["sensitivity"]
                            if max_sub is None or sub > max_sub:
                                max_sub = sub
                if max_sub is not None:
                    return max_sub
                elif "sensitivity" in rule_result["rule"]:
                    return rule_result["rule"]["sensitivity"] or 0
                else:
                    return 0
            return Sensitivity(
                    max([_cms(rule_result) for rule_result in self.matches]))


class DocumentReport(models.Model):
    path = models.CharField(max_length=2000, verbose_name="Path")
    # It could be that the meta data should not be part of the jsonfield...
    data = JSONField(null=True)

    def _str_(self):
        return self.path

    @property
    def matches(self):
        matches = self.data.get("matches")
        return MatchesMessage(
                scan_spec=matches["scan_spec"],
                handle=Handle.from_json_object(matches["handle"]),
                matched=matches["matched"],
                matches=matches["matches"]) if matches else None

    class Meta:
        verbose_name_plural = "Document reports"
