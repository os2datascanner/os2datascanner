import re
from typing import Iterator, Optional

from ..conversions.types import OutputType
from .rule import Rule, SimpleRule, Sensitivity


class RegexRule(SimpleRule):
    operates_on = OutputType.Text
    type_label = "regex"
    eq_properties = ("_expression",)

    def __init__(self, expression: str, **super_kwargs):
        super().__init__(**super_kwargs)
        self._expression = expression
        self._compiled_expression = re.compile(expression)

    @property
    def presentation_raw(self) -> str:
        return 'regular expression matching "{0}"'.format(self._expression)

    def match(self, content: str) -> Optional[Iterator[dict]]:
        if content is None:
            return

        for match in self._compiled_expression.finditer(content):
            low, high = match.span()
            match_context = content[max(low - 50, 0) : high + 50]
            yield {
                "offset": match.start(),
                "match": match.string[match.start() : match.end()],
                "context": match_context,
                "context_offset": max(low-50,0),
            }

    def to_json_object(self) -> dict:
        return dict(**super().to_json_object(), **{"expression": self._expression})

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj: dict):
        return RegexRule(
            expression=obj["expression"],
            sensitivity=Sensitivity.make_from_dict(obj),
            name=obj["name"] if "name" in obj else None,
        )
