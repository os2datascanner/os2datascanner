from typing import Iterator, Optional
import structlog
from itertools import pairwise

from .regex import RegexRule
from .utilities.context import make_context
from .rule import Rule, Sensitivity
from ..conversions.types import OutputType

logger = structlog.get_logger(__name__)

passport_regex = (r"P[A-Z<]"           # Passport and optional type identifier
                  r"(D<<|[A-Z]{3})"    # Issuing country code
                                       # (ISO 3166-1 alpha-3 for most countries,
                                       # but D<< for Germany; some territories
                                       # have special codes)
                  r"[A-Z<]{39}"        # Name

                  r"[\n \t,\-]*"       # (Some kind of line separator)

                  r"([\dA-Z<]{9})"     # Passport identifier
                  r"(\d)"              # Passport identifier check digit

                  r"(?:D<<|[A-Z]{3})"  # Holder's citizenship (same format as
                                       # issuing country code)

                  r"(\d{6})"           # Holder's date of birth (YYMMDD)
                  r"(\d)"              # Date of birth check digit

                  r"[MF<]"             # Gender of holder, if specified

                  r"(\d{6})"           # Passport expiry date (YYMMDD)
                  r"(\d)"              # Expiry date check digit

                  r"([A-Z\d<]{14})"    # Personal number field (can be empty)
                  r"([\d<])"           # Personal number check digit
                                       # (can be either 0 or < if field empty)

                  r"(\d)"              # Second line check digit
                  )


class PassportRule(RegexRule):
    type_label = "passport"
    operates_on = OutputType.MRZ

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
            checks = passport_data + [all_passport_info] + [cd_all]

            MRZ = match.string[match.start(): match.end()]

            if not all(checksum(cl, cr)
                       for i, (cl, cr) in enumerate(pairwise(checks)) if i % 2 == 0):
                logger.debug(f"{MRZ} Failed checksum")
                continue

            if country_issued == "D<<":
                # Convert Germany's weird code into a normal country code for
                # the match description
                country_issued = "DEU"
            yield {
                "match": f"Passport number {passport_number} (issued by {country_issued})",
                **make_context(match, content),
                "sensitivity": (
                    self.sensitivity.value
                    if self.sensitivity else None
                ),
            }

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
    # Special treatment for the personal number field: if the field has no
    # content, the check digit can be given as "<" instead
    if digit == "<" and all(c == "<" for c in string):
        return True

    sum = 0
    for i, char in enumerate(string):
        value = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ".index(char) if char != '<' else 0

        match i % 3:
            case 0:
                factor = 7
            case 1:
                factor = 3
            case _:
                factor = 1

        sum += value * factor
    return sum % 10 == int(digit)
