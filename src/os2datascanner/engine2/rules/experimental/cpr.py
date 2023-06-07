import structlog
from typing import Iterator, Optional

from ...conversions.types import OutputType
from os2ds_rules import CPRDetector
from ..rule import Rule, SimpleRule, Sensitivity
from ..logical import oxford_comma


logger = structlog.get_logger(__name__)


def censor(text, cpr):
    censored_cpr = cpr[0:4] + "XXXXXX"
    return text.replace(cpr, censored_cpr)


def make_context(m, text):
    low, high = m['start'], m['end']
    ctx_low, ctx_high = max(low - 50, 0), min(high + 50, len(text))
    # Extract context, remove newlines and tabs for better representation
    match_context = censor(" ".join(text[ctx_low:ctx_high].split()), m['match'])

    return {
        "offset": low,
        "context": match_context,
        "context_offset": low - ctx_low
    }


class TurboCPRRule(SimpleRule):
    '''
    This is an experimental implementation CPRRule for the next generation of scanner
    engine rules. It uses the CPRDetector implementation from the external os2ds-rules
    package. For further information, see the documentation for the os2ds-rules package.

    Note that the new rule doesn't have a 'ignore_irrelevant'-option and is more aggressive.
    '''
    type_label = "cpr_turbo"
    operates_on = OutputType.Text

    def __init__(self,
                 modulus_11: bool = False,
                 examine_context: bool = False,
                 **super_kwargs):
        super().__init__(**super_kwargs)
        self._modulus_11 = modulus_11
        self._examine_context = examine_context
        self._rule = CPRDetector(modulus_11, examine_context)

    @property
    def presentation_raw(self) -> str:
        properties = []
        if self._modulus_11:
            properties.append("modulus 11")
        if self._examine_context:
            properties.append("context check")

        if properties:
            return "CPR number (with {0})".format(oxford_comma(properties, "and"))
        else:
            return "CPR number"

    def match(self, content: str) -> Optional[Iterator[dict]]:
        if content is None:
            return

        itot = 0
        for cpr in self._rule.find_matches(content):
            itot += 1
            yield {
                "match": censor(cpr["match"], cpr["match"]),
                **make_context(cpr, content),
                "sensitivity": (
                    self.sensitivity.value
                    if self.sensitivity
                    else Sensitivity.CRITICAL.value
                   ),
                "probability": 1.0,
                }
        logger.debug(f"(experimental) Found {itot} cpr numbers in content")

    def to_json_object(self) -> dict:
        return super().to_json_object() | {
            'modulus_11': self._modulus_11,
            'examine_context': self._examine_context,
            }

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj: dict):
        return TurboCPRRule(
            modulus_11=obj.get("modulus_11", True),
            examine_context=obj.get("examine_context", False),
            sensitivity=Sensitivity.make_from_dict(obj),
            name=obj.get("name"),
        )
