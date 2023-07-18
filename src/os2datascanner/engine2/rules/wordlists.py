import re

from typing import Iterator, Optional

from ..conversions.types import OutputType
from .rule import Rule, SimpleRule, Sensitivity
from .datasets.loader import common as common_loader


class OrderedWordlistRule(SimpleRule):
    """A OrderedWordlistRule finds matches for lists of words. The words in a
    word list must appear closely together in the text and in order: the text
    "this dog is good" does not match the word list ["good", "dog"], but "this
    is a good -- perhaps even the best -- dog" does. Matches are not
    case-sensitive."""
    operates_on = OutputType.Text
    type_label = "ordered-wordlist"
    eq_properties = ("_dataset",)

    def __init__(self, dataset: str, **super_kwargs):
        super().__init__(**super_kwargs)
        self._dataset = dataset
        self._wordlists = [
                wl
                for wl in common_loader.load_dataset("wordlists", dataset)
                if wl]
        expression = "|".join(r"(\b" + ".{,32}".join(re.escape(frag) for frag in wl) + r"\b)"
                              for wl in self._wordlists)

        self._compiled_expr = re.compile(expression, re.IGNORECASE | re.DOTALL)

    @property
    def presentation_raw(self) -> str:
        return f"lists of words from dataset {self._dataset}"

    def match(self, content: str) -> Optional[Iterator[dict]]:  # noqa
        if content is None:
            return

        def _get_formatted_match(m):
            index = m.lastindex - 1
            return " ".join(self._wordlists[index])

        for m in self._compiled_expr.finditer(content):
            begin, end = m.span()
            context_begin = max(begin - 50, 0)
            context_end = min(end + 50, len(content))
            yield {
                "match": _get_formatted_match(m),
                "offset": begin,
                "context": content[context_begin:context_end],
                "context_offset": min(begin, 50)
                }

    def to_json_object(self) -> dict:
        return dict(**super().to_json_object(), dataset=self._dataset)

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj: dict):
        return OrderedWordlistRule(
            dataset=obj["dataset"],
            sensitivity=Sensitivity.make_from_dict(obj),
            name=obj["name"] if "name" in obj else None,
        )
