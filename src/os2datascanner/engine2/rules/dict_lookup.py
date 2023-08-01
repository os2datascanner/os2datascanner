from .rule import Rule, SimpleRule, Sensitivity
from ..conversions.types import OutputType


class DictLookupRule(SimpleRule):
    def __init__(
            self, prop: str, rule: Rule, **kwargs):
        super().__init__(**kwargs)
        self._prop = prop
        self._rule = rule

    def match(self, value: dict):
        if self._prop not in value:
            return

        # This is the magic that flattens a Rule into a SimpleRule: we call the
        # underlying Rule with a single representation, the dictionary value
        # we've extracted, and we return success only if that was enough
        representations = {
            OutputType.Text.value: value[self._prop]
        }
        conclusion, all_matches = self._rule.try_match(representations)

        if conclusion is True:
            for _, rms in all_matches:
                yield from (r for r in rms if r["match"])

    def to_json_object(self):
        return super().to_json_object() | {
            "property": self._prop,
            "rule": self._rule.to_json_object(),
        }

    @classmethod
    def from_json_object(cls, obj):
        return cls(
                prop=obj["property"],
                rule=Rule.from_json_object(obj["rule"]),

                sensitivity=Sensitivity.make_from_dict(obj),
                name=obj["name"] if "name" in obj else None)


class EmailHeaderRule(DictLookupRule):
    type_label = "email-header"

    operates_on = OutputType.EmailHeaders

    @property
    def presentation_raw(self):
        return (f"email header value \"{self._prop}\""
                f" matches the rule \"{self._rule.presentation}\"")


Rule.json_handler(EmailHeaderRule.type_label)(EmailHeaderRule.from_json_object)
