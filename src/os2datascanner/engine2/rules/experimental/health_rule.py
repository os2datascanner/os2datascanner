import structlog
from typing import Iterator, Optional

from ...conversions.types import OutputType
from ..rule import Rule, SimpleRule, Sensitivity
from ..datasets.loader import common as common_loader
from os2ds_rules.wordlist_rule import WordListRule

logger = structlog.get_logger(__name__)


class TurboHealthRule(SimpleRule):
    """
    This rule searches for health-terms based on a revised version
    of the scraped dataset from the sitemap of Laegehaandbogen.

    Implementation-wise it uses the `WordListRule` from the os2ds-rules
    package and will only match on single words. No complicated sentence
    analysis or use of context here. Just pure speed.
    """
    type_label = "health_turbo"
    operates_on = OutputType.Text

    def __init__(self, **super_kwargs):
        super().__init__(**super_kwargs)
        dataset = common_loader.load_dataset("wordlists", "da_20211018_laegehaandbog_stikord")
        self._rule = WordListRule([str.lower(word) for word in dataset])

    def match(self, content: str) -> Optional[Iterator[dict]]:
        if not content:
            return

        yield from self._rule.find_matches(content)

    @property
    def presentation_raw(self) -> str:
        return "Turbo Health Rule"

    def to_json_object(self) -> dict:
        return super().to_json_object()

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj: dict):
        return TurboHealthRule(
            sensitivity=Sensitivity.make_from_dict(obj))
