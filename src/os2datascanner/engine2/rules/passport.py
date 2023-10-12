from typing import Iterator, Optional
import structlog

from .regex import RegexRule
from .utilities.context import make_context
from .rule import Rule, Sensitivity

logger = structlog.get_logger(__name__)

dk_passport_regex = r"P<DNK[A-Z<]{39}[\n \t,]?(\d{9})(\d)DNK(\d{6})(\d)[MF<](\d{6})(\d)([A-Z\d<]{14})(\d)(\d)"  # noqa: E501 line too long
generic_passport_regex = r"P[A-Z<]([A-Z]{3})[A-Z<]{39}[\n \t,]?([\dA-Z]{9})(\d)([A-Z]{3})(\d{6})(\d)[MF<](\d{6})(\d)([A-Z\d<]{14})(\d)(\d)"  # noqa: E501 line too long


class PassportRule(RegexRule):
    type_label = "passport MRZ"

    def __init__(self, danish: bool = True, **super_kwargs):
        self._passport_regex = dk_passport_regex if danish else generic_passport_regex
        super.__init__(self._passport_regex, **super_kwargs)
        self._danish = danish

    @property
    def presentation_raw(self) -> str:
        if self._danish:
            return "Danish Passport MRZ"
        else:
            return "Passport MRZ"

    def match(self, content: str) -> Optional[Iterator[dict]]:  # noqa: CCR001,E501 too high cognitive complexity
        if content is None:
            return

        for match in self._compiled_expression.finditer(content):
            if self._danish:
                (passport_number, cd1, birthday,
                 cd2, expiration_date, cd3, personal_number,
                 cd4, cd_all) = match.groups()
            else:
                (country_issued, passport_number, cd1,
                 nationality, birthday, cd2, expiration_date,
                 cd3, personal_number, cd4, cd_all) = match.groups()

            MRZ = match.string[match.start(): match.end()]

            if (not checksum(passport_number, cd1)  # noqa: ECE001 Expression too complex
                or not checksum(birthday, cd2)
                or not checksum(expiration_date, cd3)
                or not checksum(personal_number, cd4)
               or not checksum(passport_number + cd1 + birthday + cd2 + expiration_date + cd3 + personal_number + cd4, cd_all)):  # noqa: E501 line too long
                logger.debug(f"{MRZ} failed checksum")
                continue

            yield {
                "match": MRZ,
                **make_context(match, content),

                "sensitivity": (
                    self.sensitivity.value
                    if self.sensitivity else None
                ),

            }

    def to_json_object(self) -> dict:
        return dict(
            **super(RegexRule, self).to_json_object(),
            danish=self._danish
        )

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj: dict):
        return PassportRule(
            danish=obj.get("danish", True),
            sensitivity=Sensitivity.make_from_dict(obj),
            name=obj["name"] if "name" in obj else None,
        )


def checksum(string: str, digit) -> bool:  # noqa: CCR001 too high cognitive complexity
    sum = 0
    for i, char in enumerate(string):
        value = 0
        if char >= 'A' and char <= 'Z':
            value = char - 'A' + 10
        if char >= '0' and char <= '9':
            value = char - '0'

        if i % 3 == 0:
            factor = 7
        elif i % 3 == 1:
            factor = 3
        else:
            factor = 1

        sum += value * factor
    return sum == int(digit)
