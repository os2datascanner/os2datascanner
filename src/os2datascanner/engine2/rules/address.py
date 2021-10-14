import regex

from ..conversions.types import OutputType
from .rule import Rule, SimpleRule, Sensitivity
from .datasets.loader import common as common_loader

# see https://regex101.com/r/zJBsXw/9 for examples of matches
# \p{Lu} match a upper case unicode letter, see
# https://www.regular-expressions.info/unicode.html#category
# rules for addresses
# https://danmarksadresser.dk/regler-og-vejledning/adresser/
# Match whitespace except newlines
_whitespace = r"[^\S\n\r]+"
_optional_comma = r",?"
_optional_whitespace = r"[^\S\n\r]?"

# match a number prepended to a street name, like '10.' or '10-'
_prepend_number = r"\d*[\.-]"
_street_name = r"\p{Lu}\p{L}*[\.\/-]?"
_simple_name = r"\p{Lu}\p{L}*[\.]?"
_house_number = r"[1-9][0-9]*[a-zA-Z]?"
_floor = r"[0-9]{{0,3}}\.?{0}(?:tv|th|mf|sal|[0-9]*)".format(_whitespace)
_zip_code = r"[1-9][0-9][0-9][0-9]"
_street_address = (
    r"(?P<street_name>(?:{0}{ws})?(?:{1}{ws})+)". format(
        _prepend_number,
        _street_name,
        ws=_optional_whitespace) +
    r"(?P<house_number>{0})?".format(_house_number) )
_floor_number = r"(?P<floor>{0}{1})?".format(_whitespace,_floor)
_zip_city = r"(?P<zip_code>{0}){1}(?P<city>(?:{2}{3})+)".format(
    _zip_code,
    _whitespace,
    _simple_name,
    _optional_whitespace
)
full_address_regex = regex.compile(
    r"\b" + _street_address + _optional_comma +  _floor_number + _optional_comma +
    r"(" + _optional_whitespace + _zip_city + r")?" + r"\b",
    regex.UNICODE
)


def match_full_address(text):
    """Return possible address matches in the given text as a `set`"""

    def strip_or_empty(string):
        return string.strip() if string else ""

    matches = set()
    it = full_address_regex.finditer(text, overlapped=False)
    for m in it:
        street_address = strip_or_empty(m.group("street_name"))
        house_number = strip_or_empty(m.group("house_number"))
        floor = strip_or_empty(m.group("floor"))
        zip_code = strip_or_empty(m.group("zip_code"))
        city = strip_or_empty(m.group("city"))

        matched_text = m.group(0)
        matches.add(
            (street_address, house_number, floor, zip_code, city, matched_text)
        )
    return matches


class AddressRule(SimpleRule):
    """Represents a rule which scans for addresses in text.

    The rule loads a list of addresses and matches against them to determine the
    sensitivity level of the matches.

    If both a street and number is found or the street, the sensitivity is
    `CRITICAL`. If only a street is found(matched against the street list), the
    sensitivity is `PROBLEM`

    """
    operates_on = OutputType.Text
    type_label = "address"
    eq_properties = ("_whitelist", "_blacklist",)


    def __init__(self, whitelist=None, blacklist=None, **super_kwargs):
        super().__init__(**super_kwargs)

        # Convert list of str to upper case and to sets for efficient lookup
        self.street_names = set(map(str.upper,
                common_loader.load_dataset(
                        "addresses", "da_addresses")))

        self._whitelist = [n.upper() for n in (whitelist or [])]
        self._blacklist = [n.upper() for n in (blacklist or [])]

    @property
    def presentation_raw(self):
        return "personal address"

    def match(self, text):

        def is_address_fragment(fragment, candidates):
            fragment = fragment.upper()
            return (fragment in candidates
                    and fragment not in self._whitelist)

        # First, check for full address
        addresses = match_full_address(text)
        for address in addresses:
            street_name = address[0]
            house_number = address[1] if address[1] else ''
            floor = address[2] if address[2] else ''
            zip_code = address[3] if address[4] else ''
            city = address[4] if address[4] else ''

            street_address = f"{street_name} {house_number}"
            full_address = (
                f"{street_address}{', ' + floor if floor else ''}, "
                f"{zip_code} {city}"
            )

            # Store the original matching text
            matched_text = address[5]

            street_match = is_address_fragment(street_name, self.street_names)
            street_name_up = street_name.upper()
            is_blacklisted = any([street_name_up in b for b in self._blacklist])
            if (street_match and house_number) or is_blacklisted:
                sensitivity = Sensitivity.CRITICAL
            elif street_match:
                sensitivity = Sensitivity.PROBLEM
            else:
                continue

            yield {
                "match": matched_text,
                "sensitivity": sensitivity.value
            }


    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "whitelist": self._whitelist,
            "blacklist": self._blacklist
        })

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj):
        return AddressRule(
                whitelist=obj["whitelist"],
                blacklist=obj["blacklist"],
                sensitivity=Sensitivity.make_from_dict(obj))
