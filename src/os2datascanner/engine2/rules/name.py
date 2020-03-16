# coding=utf-8
# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )

"""Rules for name scanning."""

import os
import regex

from ..conversions.types import OutputType
from .rule import Rule, SimpleRule, Sensitivity
from .datasets.loader import common as common_loader

# Match whitespace except newlines
_whitespace = "[^\\S\\n\\r]+"
_simple_name = "\\p{Uppercase}(\\p{L}+|\\.?)"
_name = "{0}(-{0})?".format(_simple_name)
full_name_regex = regex.compile(
    "\\b(?P<first>" + _name + ")" +
    "(?P<middle>(" + _whitespace + _name + "){0,3})" +
    "(?P<last>" + _whitespace + _name + "){1}\\b", regex.UNICODE)


def match_full_name(text):
    """Return possible name matches in the given text."""
    matches = set()
    it = full_name_regex.finditer(text, overlapped=False)
    for m in it:
        first = m.group("first")
        try:
            middle = m.group("middle")
        except IndexError:
            middle = ''
        if middle:
            middle_split = tuple(
                regex.split('\s+', middle.lstrip(), regex.UNICODE))
        else:
            middle_split = ()
        last = m.group("last").lstrip()
        matched_text = m.group(0)
        matches.add((first, middle_split, last, matched_text))
    return matches


class NameRule(SimpleRule):
    """Represents a rule which scans for Full Names in text.

    The rule loads a list of names from first and last name files and matches
    names against them to determine the sensitivity level of the matches.
    Matches against full, capitalized, names with up to 2 middle names.
    """
    operates_on = OutputType.Text
    type_label = "name"
    eq_properties = ("_whitelist", "_blacklist",)

    def __init__(self, whitelist=[], blacklist=[], **super_kwargs):
        super().__init__(**super_kwargs)

        # Convert to sets for efficient lookup
        m = set(
                common_loader.load_dataset(
                        "names", "20140101_dst_fornavne-mænd"))
        k = set(
                common_loader.load_dataset(
                        "names", "20140101_dst_fornavne-kvinder"))
        e = set(
                common_loader.load_dataset(
                        "names", "20140101_dst_efternavne"))
        f = m.union(k)

        self.last_names = e
        self.first_names = f
        self.all_names = f.union(e)

        self._whitelist = [n.upper() for n in whitelist]
        self._blacklist = [n.upper() for n in blacklist]

    @property
    def presentation_raw(self):
        return "personal name"

    def match(self, text):
        matches = set()
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
                #sensitivity = Sensitivity.OK
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
        return matches

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "whitelist": self._whitelist,
            "blacklist": self._blacklist
        })

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj):
        return NameRule(
                whitelist=obj["whitelist"],
                blacklist=obj["blacklist"],
                sensitivity=Sensitivity.make_from_dict(obj))
