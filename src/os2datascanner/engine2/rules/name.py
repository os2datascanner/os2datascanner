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
    """Represents a rule which scans for Full Names in text.

    The rule loads a list of names from first and last name files and matches
    names against them to determine the sensitivity level of the matches.
    Matches against full, capitalized, names with up to three middle names.
    A name in this context, is a capitalized Word.

    Last, the text is checked for any standalone names, ie. single capitalized
    Words

    Note that name matches internally are stored as a `set`, thus matches are
    not returned in order.

    """
    operates_on = OutputType.Text
    type_label = "name"
    eq_properties = ("_whitelist", "_blacklist",)

    def __init__(self, whitelist=None, blacklist=None, **super_kwargs):
        super().__init__(**super_kwargs)

        # Convert list of str to upper case and to sets for efficient lookup
        self.last_names = None
        self.first_names = None
        self.all_names = None

        self._whitelist = frozenset(n.upper() for n in (whitelist or []))
        self._blacklist = frozenset(n.upper() for n in (blacklist or []))

    @property
    def presentation_raw(self):
        return "personal name"

    def _load_datasets(self):
        if self.all_names is None:
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
            self.all_names = f.union(e)

    def match(self, text):  # noqa: CCR001, too high cognitive complexity
        self._load_datasets()
        unmatched_text = text

        def is_name_fragment(fragment, candidates, use_blacklist=True):
            fragment = fragment.upper()
            if use_blacklist and fragment in self._blacklist:
                return True
            else:
                return (fragment in candidates
                        and fragment not in self._whitelist)

        # First, check for whole names, i.e. at least Firstname + Lastname
        names = match_full_name(text)
        for name in names:
            # Match each name against the list of first and last names
            first_name = name[0]
            middle_names = [n for n in name[1]]
            last_name = name[2] if name[2] else ""

            # Store the original matching text
            matched_text = name[3]

            first_match = is_name_fragment(first_name, self.first_names)
            last_match = is_name_fragment(last_name, self.last_names)
            middle_match = any(
                [is_name_fragment(n, self.all_names) for n in middle_names]
            )
            # But what if the name is Word Firstname Lastname?
            while middle_match and not first_match:
                old_name = first_name
                first_name = middle_names.pop(0)
                first_match = is_name_fragment(first_name, self.first_names)
                middle_match = any(
                    [is_name_fragment(n, self.all_names) for n in middle_names]
                )
                matched_text = matched_text.lstrip(old_name)
                matched_text = matched_text.lstrip()
            # Or Firstname Lastname Word?
            while middle_match and not last_match:
                old_name = last_name
                last_name = middle_names.pop()
                last_match = is_name_fragment(last_name, self.last_names)
                middle_match = any(
                    [is_name_fragment(n, self.all_names) for n in middle_names]
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
            is_blacklisted = any([b in full_name_up for b in self._blacklist])
            # Name match is always high sensitivity
            # and occurs only when first and last name are in the name lists
            # Set sensitivity according to how many of the names were found
            # in the names lists
            if (first_match and last_match) or is_blacklisted:
                sensitivity = Sensitivity.CRITICAL
            elif first_match or last_match or middle_match:
                sensitivity = Sensitivity.PROBLEM
            else:
                continue

            # Update remaining, i.e. unmatched text
            unmatched_text = unmatched_text.replace(matched_text, "", 1)

            yield {
                "match": matched_text,
                "sensitivity": sensitivity.value
            }
        # Full name match done. Now check if there's any standalone names in
        # the remaining, i.e. so far unmatched string.
        name_regex = regex.compile(_name)
        it = name_regex.finditer(unmatched_text, overlapped=False)
        for m in it:
            matched = m.group(0)
            if is_name_fragment(matched.upper(), self.all_names):
                yield {
                    "match": matched,
                    "sensitivity": self.sensitivity
                }

    def to_json_object(self):
        return dict(
            **super().to_json_object(),
            whitelist=list(self._whitelist),
            blacklist=list(self._blacklist),
        )

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj):
        return NameRule(
                whitelist=frozenset(obj["whitelist"]),
                blacklist=frozenset(obj["blacklist"]),
                sensitivity=Sensitivity.make_from_dict(obj))
