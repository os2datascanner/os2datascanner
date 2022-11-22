import regex

from ..conversions.types import OutputType
from .rule import Rule, SimpleRule, Sensitivity
from .datasets.loader import common as common_loader

_whitespace = (
        r"[^\S\n\r]+"  # One or more of every whitespace character (apart from
                       # new lines)
)

_simple_name = (
        r"\p{Lu}"          # One upper-case letter...
        r"(?:\p{L}+|\.?)"  # followed by one or more letters, a full stop, or
                           # nothing
)
# (for example, "Joe", "Bloggs", "Bulwer", "K.", "J", or "Edward")

_name = (
        rf"{_simple_name}"        # A simple_name...
        rf"(?:-{_simple_name})?"  # optionally hyphenated with another one
)
# (for example, "Jens", "Bulwer-Lytton", "You", "United", or "B.-L.")

full_name_regex = regex.compile(  # noqa: ECE001, expression is too complex
    rf"\b(?P<first>{_name})"               # A name at the start of a word...
    rf"(?P<middle>({_whitespace}{_name})"
    r"{0,3})"                              # followed by zero to three more
                                           # whitespace-separated names...
    rf"(?P<last>{_whitespace}{_name})\b"   # followed by another name and the
                                           # end of the word
)
# (for example, "Joe Bloggs", "Josef K.", "L. Frank Baum", "Edward George Earle
# Lytton Bulwer-Lytton", "Jens J-J. Jens-Jens Jens Jensen", "United Kingdom",
# or "You Are A Winner")


def match_full_name(text):
    """Return possible name matches in the given text as a `set`."""

    def strip_or_empty(string):
        return string.strip() if string else ""

    matches = set()
    it = full_name_regex.finditer(text, overlapped=False)
    for m in it:
        first = strip_or_empty(m.group("first"))
        middle = strip_or_empty(m.group("middle"))
        if middle:
            middle_split = tuple(
                regex.split(r'\s+', middle.lstrip(), regex.UNICODE))
        else:
            middle_split = ()
        last = strip_or_empty(m.group("last"))
        matched_text = m.group(0)
        matches.add((first, middle_split, last, matched_text))
    return matches


class NameRule(SimpleRule):
    """A NameRule looks for strings of text that resemble Danish names. It
    couples a regular expression-driven scan for name-like tokens with a
    dataset used to determine if those tokens are plausible names."""
    operates_on = OutputType.Text
    type_label = "name"
    eq_properties = ("_whitelist", "_blacklist",)

    def __init__(
            self,
            expansive=None,  # Also find name-like strings not in the dataset?
            whitelist=None,
            blacklist=None,
            **super_kwargs):
        super().__init__(**super_kwargs)

        # Convert list of str to upper case and to sets for efficient lookup
        self.last_names = None
        self.first_names = None

        self._expansive = expansive
        self._whitelist = frozenset(n.upper() for n in (whitelist or []))
        self._blacklist = frozenset(n.upper() for n in (blacklist or []))

    @property
    def presentation_raw(self):
        return "personal name"

    def _load_datasets(self):
        if self.first_names is None:
            # Convert list of str to upper case and to sets for efficient
            # lookup
            m = set(map(str.upper,
                    common_loader.load_dataset(
                            "names", "da_20140101_dst_fornavne-mænd")))
            k = set(map(str.upper,
                    common_loader.load_dataset(
                            "names", "da_20140101_dst_fornavne-kvinder")))
            e = set(map(str.upper,
                    common_loader.load_dataset(
                            "names", "da_20140101_dst_efternavne")))
            f = m.union(k)

            self.last_names = e
            self.first_names = f

    def match(self, text):  # noqa: CCR001, too high cognitive complexity
        self._load_datasets()
        unmatched_text = text

        def is_name_component(
                component: str,
                *candidate_sets: set[str]):
            component = component.upper()
            if component in self._blacklist:
                return True
            elif component in self._whitelist:
                return False
            else:
                return any(component in cs for cs in candidate_sets)

        # First, check for whole names, i.e. at least Firstname + Lastname
        names = match_full_name(text)
        for name in names:
            # Match each name against the list of first and last names
            first_name = name[0]
            middle_names = [n for n in name[1]]
            last_name = name[2] if name[2] else ""

            # Store the original matching text
            matched_text = name[3]

            first_match = is_name_component(first_name, self.first_names)
            last_match = is_name_component(last_name, self.last_names)
            middle_match = any(
                is_name_component(n, self.first_names, self.last_names)
                for n in middle_names
            )
            # But what if the name is Word Firstname Lastname?
            while middle_match and not first_match:
                old_name = first_name
                first_name = middle_names.pop(0)
                first_match = is_name_component(first_name, self.first_names)
                middle_match = any(
                    is_name_component(n, self.first_names, self.last_names)
                    for n in middle_names
                )
                matched_text = matched_text.lstrip(old_name)
                matched_text = matched_text.lstrip()
            # Or Firstname Lastname Word?
            while middle_match and not last_match:
                old_name = last_name
                last_name = middle_names.pop()
                last_match = is_name_component(last_name, self.last_names)
                middle_match = any(
                    is_name_component(n, self.first_names, self.last_names)
                    for n in middle_names
                )
                matched_text = matched_text.rstrip(old_name)
                matched_text = matched_text.rstrip()

            if middle_names:
                full_name = "%s %s %s" % (
                    first_name, " ".join(middle_names), last_name
                )
            else:
                full_name = "%s %s" % (first_name, last_name)

            full_name_up = full_name.upper()
            # Check if name is blacklisted.
            # The name is blacklisted if there exists a string in the
            # blacklist which is contained as a substring of the name.
            is_blacklisted = any(b in full_name_up for b in self._blacklist)
            # Name match is always high probability
            # and occurs only when first and last name are in the name lists
            # Set probability according to how many of the names were found
            # in the names lists
            if (first_match and last_match) or is_blacklisted:
                probability = 1.0
            elif first_match or last_match or middle_match:
                probability = 0.5
            else:
                continue

            # If we have to do a second pass, cut this matched name out to
            # avoid duplicates
            if self._expansive:
                unmatched_text = unmatched_text.replace(matched_text, "", 1)

            yield {
                "match": matched_text,
                "probability": probability,
                "sensitivity": (
                    self.sensitivity.value if self.sensitivity else None
                ),
            }
        if self._expansive:
            # Full name match done. Now check if there's any standalone names
            # in the remaining, i.e. so far unmatched string.
            name_regex = regex.compile(_name)
            it = name_regex.finditer(unmatched_text, overlapped=False)
            for m in it:
                matched = m.group(0)
                if is_name_component(
                        matched.upper(), self.first_names, self.last_names):
                    yield {
                        "match": matched,
                        "probability": 0.1,
                        "sensitivity": (
                            self.sensitivity.value
                            if self.sensitivity else None
                        ),
                    }

    def to_json_object(self):
        return dict(
            **super().to_json_object(),
            whitelist=list(self._whitelist),
            blacklist=list(self._blacklist),
            expansive=self._expansive
        )

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj):
        return NameRule(
                whitelist=frozenset(obj["whitelist"]),
                blacklist=frozenset(obj["blacklist"]),
                expansive=obj.get("expansive", None),
                sensitivity=Sensitivity.make_from_dict(obj))
