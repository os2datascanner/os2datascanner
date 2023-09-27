import re

from typing import Iterator, Optional

from ..conversions.types import OutputType
from .rule import Rule, SimpleRule, Sensitivity
from .datasets.loader import common as common_loader


def load_words(dataset):
    """
    Loads a dataset as an iterable.

    The content of the dataset is flattened, if it contains
    any structured data.
    """
    loaded = common_loader.load_dataset("wordlists", dataset)

    def _flatten(elem):
        match elem:
            case list():
                for e in elem:
                    yield from _flatten(e)
            case _:
                yield str(elem).lower()

    yield from _flatten(loaded)


class OrderedWordlistRule(SimpleRule):
    """
    A OrderedWordlistRule finds matches for a single list of words.

    As of #57536 this now works on a simple flat list of words
    instead of using lists of lists of words.

    Matches are not case-sensitive.
    """
    operates_on = OutputType.Text
    type_label = "ordered-wordlist"
    eq_properties = ("_dataset",)

    def __init__(self, dataset: str, **super_kwargs):
        super().__init__(**super_kwargs)
        self._dataset = dataset
        self._wordlists = frozenset(load_words(dataset))
        self._compiled_expr = re.compile(r"\w+", re.IGNORECASE | re.DOTALL)

    @property
    def presentation_raw(self) -> str:
        return f"lists of words from dataset {self._dataset}"

    def match(self, content: str) -> Optional[Iterator[dict]]:  # noqa

        if content is None:
            return

        for m in self._compiled_expr.finditer(content):
            lowered = str(m.group()).lower()
            if lowered in self._wordlists:
                begin, end = m.span()
                context_begin = max(begin - 50, 0)
                context_end = min(end + 50, len(content))
                yield {
                    "match": m.group(),
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
