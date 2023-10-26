from typing import Iterator, Optional
import structlog
from itertools import pairwise

from .regex import RegexRule
from .utilities.context import make_context
from .rule import Rule, Sensitivity

logger = structlog.get_logger(__name__)

# dk_passport_regex = r"P<DNK[A-Z<]{39}[\n \t,]?(\d{9})(\d)DNK(\d{6})(\d)[MF<](\d{6})(\d)([A-Z\d<]{14})(\d)(\d)"  # noqa: E501 line too long
passport_regex = (r"P[A-Z<kx]([A-Z]{3})[A-Z<kx]{39}[\n \t,]?"
                  r"([\dA-Z]{9})(\d)[A-Z]{3}(\d{6})(\d)[MF<kx]"
                  r"(\d{6})(\d)([A-Z\d<kx]{14})(\d)(\d)")


class PassportRule(RegexRule):
    type_label = "passport MRZ"

    def __init__(self, **super_kwargs):
        super().__init__(passport_regex, **super_kwargs)
        self._passport_regex = passport_regex

    @property
    def presentation_raw(self) -> str:
        return "Passport MRZ"

    def match(self, content: str) -> Optional[Iterator[dict]]:  # noqa: CCR001,E501 too high cognitive complexity
        if content is None:
            return

        for match in self._compiled_expression.finditer(content):
            country_issued, *passport_data, cd_all = match.groups()
            passport_number = passport_data[0]

            all_passport_info = "".join(passport_data)
            checks = pairwise(passport_data + [all_passport_info] + [cd_all])
            print(checks)

            MRZ = match.string[match.start(): match.end()]

            if not any(checksum(*check) for check in checks):
                logger.debug(f"{MRZ} Failed checksum")
                continue

            yield {
                "match": f"Passport number {passport_number} (issued by {country_issued})",
                **make_context(match, content),

                "sensitivity": (
                    self.sensitivity.value
                    if self.sensitivity else None
                ),

            }
            print(MRZ, "matched")

    def to_json_object(self):
        return super().to_json_object()

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj: dict):
        return PassportRule(
            sensitivity=Sensitivity.make_from_dict(obj),
            name=obj["name"] if "name" in obj else None,
        )


def checksum(string: str, digit) -> bool:  # noqa: CCR001 too high cognitive complexity
    sum = 0
    for i, char in enumerate(string):
        value = 0
        if char >= 'A' and char <= 'Z':
            value = ord(char) - ord('A') + 10
        if char >= '0' and char <= '9':
            value = int(char)

        if i % 3 == 0:
            factor = 7
        elif i % 3 == 1:
            factor = 3
        else:
            factor = 1

        sum += value * factor
    return sum % 10 == int(digit)
