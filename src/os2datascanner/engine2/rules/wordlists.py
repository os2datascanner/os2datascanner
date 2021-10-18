from typing import Iterator, Optional

from ..conversions.types import OutputType
from .rule import Rule, SimpleRule, Sensitivity
from .datasets.loader import common as common_loader


def _match_wordlist(wordlist, content, folded_content):
    slices = []
    start_at = 0
    end_at = len(folded_content)
    for word in wordlist:
        try:
            index = folded_content[start_at:end_at].index(word.casefold())
            true_index = start_at + index
            start_at = true_index + len(word)
            end_at = start_at + 32
            slices.append(slice(true_index, start_at))
        except ValueError:
            return

    starts_at = slices[0].start
    yield {
        "match": " ".join(wordlist),
        "offset": slices[0].start,
        "context": content[
                slice(max(starts_at - 50, 0), slices[-1].stop + 50)],
        "context_offset": min(starts_at, 50)
    }


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

    @property
    def presentation_raw(self) -> str:
        return f"lists of words from dataset {self._dataset}"

    def match(self, content: str) -> Optional[Iterator[dict]]:
        if content is None:
            return
        folded_content = content.casefold()

        for wordlist in self._wordlists:
            yield from _match_wordlist(wordlist, content, folded_content)

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
