from typing import Iterator, List, Match, Optional, Tuple, Dict, Union
import re
from itertools import chain
from enum import Enum, unique
from collections.abc import Iterable
import logging

from .rule import Rule, Sensitivity
from .regex import RegexRule
from .logical import oxford_comma
from .utilities.cpr_probability import modulus11_check, CprProbabilityCalculator

logger = logging.getLogger(__name__)
cpr_regex = r"\b(\d{2}[\s]?\d{2}[\s]?\d{2})(?:[\s\-/\.]|\s\-\s)?(\d{4})\b"
calculator = CprProbabilityCalculator()


# if the sourronding context contains some of these, we get suspicious.
# fmt: off
# check if these delimiters are balanced
_pre_delim = ("(", "[", "{", "<", "<?", "<%", "/*", )
_post_delim = (")", "]", "}", ">", "?>", "%>", "*/", )
# any of these symbols in the context result in probability=0
_operators = ("+", "-", )
_symbols = ("!", "#", "%", )
_all_symbols = _operators + _symbols
# fmt: on


@unique
class Context(Enum):
    WHITELIST = 1
    UNBALANCED = 2
    WRONG_CASE = 3
    NUMBER = 4
    SYMBOL = 5
    BLACKLIST = 6
    PROBABILITY_CALC = 7

    # XXX custom formatter, like __str__ or __format__(self, format_spec), for
    # printing only the enum name would be nice.


class CPRRule(RegexRule):
    type_label = "cpr"
    WHITELIST_WORDS = {"cpr", }
    BLACKLIST_WORDS = {"p-nr", "p.nr", "p-nummer", "pnr", }

    def __init__(
        self,
        modulus_11: bool = True,
        ignore_irrelevant: bool = True,
        examine_context: bool = True,
        whitelist: Union[bool, List[str]] = True,
        blacklist: Union[bool, List[str]] = True,
        **super_kwargs,
    ):
        super().__init__(cpr_regex, **super_kwargs)
        self._modulus_11 = modulus_11
        self._ignore_irrelevant = ignore_irrelevant
        self._examine_context = examine_context
        # self._whitelist is either a set(str) or False
        self._whitelist = (
            self.WHITELIST_WORDS if whitelist is True else (
                set(whitelist) if isinstance(whitelist, Iterable)
                else whitelist
            ))
        self._blacklist = (
            self.BLACKLIST_WORDS if blacklist is True else (
                set(blacklist) if isinstance(blacklist, Iterable)
                else blacklist
        ))

    @property
    def presentation_raw(self) -> str:
        properties = []
        if self._modulus_11:
            properties.append("modulus 11")
        if self._ignore_irrelevant:
            properties.append("relevance check")
        if self._examine_context:
            properties.append("context check")

        if properties:
            return "CPR number (with {0})".format(oxford_comma(properties, "and"))
        else:
            return "CPR number"

    def match(self, content: str) -> Optional[Iterator[dict]]:
        if content is None:
            return

        # If there's p-nr or anthore blacklist anywhere in content, assume
        # there's no valid CPR
        if self._examine_context and self._blacklist and any(
            w in content.lower() for w in self._blacklist
        ):
            logger.info("Content contains a word from the blacklist "
                        f"[{self._blacklist}]")
            return

        imatch = 0
        for itot, m in enumerate(self._compiled_expression.finditer(content), 1):
            cpr = m.group(1).replace(" ", "") + m.group(2)
            if self._modulus_11:
                mod11, reason =  modulus11_check(cpr)
                if not mod11:
                    logger.info(f"{cpr} failed modulus11 check due to {reason}")
                    continue

            probability = 1.0
            if self._ignore_irrelevant:
                probability = calculator.cpr_check(cpr, do_mod11_check = False)
                if isinstance(probability, str):
                    logger.info(f"{cpr} is not valid cpr due to {probability}")
                    continue

            cpr = cpr[0:4] + "XXXXXX"
            low, high = m.span()
            # only examine context if there is any
            if self._examine_context and len(content) > (high - low):
                p, ctype = self.examine_context(m)
                # determine if probability stems from context or calculator
                probability = p if p is not None else probability
                ctype = ctype if ctype != [] else Context.PROBABILITY_CALC
                logger.info(f"{cpr} with probability {probability} from context "
                            f"due to {ctype}")


            # Extract context.
            match_context = content[max(low - 50, 0) : high + 50]
            match_context = self._compiled_expression.sub(
                "XXXXXX-XXXX", match_context
            )

            if probability:
                imatch += 1
                yield {
                    "offset": m.start(),
                    "match": cpr,
                    "context": match_context,
                    "context_offset": m.start() - low,
                    "sensitivity": (
                        self.sensitivity.value
                        if self.sensitivity
                        else self.sensitivity
                    ),
                    "probability": probability,
                }
            logger.info(f"{itot} cpr-like numbers, "
                        f"of which {imatch} had a probabiliy > 0")

    def examine_context(
        self, match: Match[str]
    ) -> Tuple[Optional[float], List[tuple]]:
        """Estimate a probality (0-1) based on the context of the match

        Returns 0.0 if any of the following conditions are found
        - pre-context ends with a variation of `p-nr`
        - There are unmatched delimiters, like () or {}
        - The CPR-nr is surrounded by a number that doesn't resembles a CPR
        - The word before or after is not either: lower-, title- or upper-case.

        But returns 1.0 if
        - pre-context contains "cpr" or any other whitelist words
        """

        probability = None
        words, symbols = self.extract_surrounding_words(match, n_words=3)
        ctype = []

        # test if a whitelist-word is found in the context words.
        # combine the list of 'pre' & 'post' keys in words dict.
        words_lower = [w.lower() for w in chain.from_iterable(words.values())]
        if self._whitelist:
            for w in self._whitelist:
                for cw in words_lower:
                    if w in cw:
                        ctype.append((Context.WHITELIST, cw))
                        return 1.0, ctype

        # test for balanced delimiters
        delimiters = 0
        for w in chain.from_iterable(symbols.values()):
            if w.startswith(_pre_delim):
                delimiters += 1
            elif w.endswith(_pre_delim):
                delimiters += 1
            elif w.startswith(_post_delim):
                delimiters -= 1
            elif w.endswith(_post_delim):
                delimiters -= 1
            elif w in _all_symbols:
                ctype.append((Context.SYMBOL, w))
                probability = 0.0
        if delimiters != 0:
            ctype.append((Context.UNBALANCED, delimiters))
            probability = 0.0

        # only do context checking on surrounding words
        for w in [words["pre"][-1], words["post"][0]]:
            if w == "" or self._compiled_expression.match(w):
                continue
            # this check is newer reached due to '\w' splitting
            elif w.endswith(_all_symbols) or w.startswith(_all_symbols):
                ctype.append((Context.SYMBOL, w))
                probability = 0.0
            # test if surrounding word is a number (and not looks like a cpr)
            elif is_number(w):
                probability = 0.0
                ctype.append((Context.NUMBER, w))
            elif not is_alpha_case(w):
                # test for case, ie Magenta, magenta, MAGENTA are ok, but not MaGenTa
                # nor magenta10. w must not be empty string
                probability = 0.0
                ctype.append((Context.WRONG_CASE, w))
            else:
                pass

        return probability, ctype

    def extract_surrounding_words(
        self, match: Match[str], n_words: int = 2
    ) -> Tuple[Dict[str, list], Dict[str, list]]:
        """Extract at most `n_words` before and after the match

        Return a dict with words and one with symbols
        """

        # get full content
        content = match.string
        low, high = match.span()
        # get previous/next n words
        pre = " ".join(content[max(low-50,0):low].split()[-n_words:])
        post = " ".join(content[high:high+50].split()[:n_words])

        # split in two capture groups: (word, symbol)
        # Ex: 'The brown, fox' ->
        # [('The', ''), ('brown', ''), ('', ','), ('fox', '')]
        word_str = r"(\w+(?:[-\./]\w*)*)"
        symbol_str = r"([^\w\s\.\"])"
        split_str = r"|".join([word_str, symbol_str])
        pre_res = re.findall(split_str, pre)
        post_res = re.findall(split_str, post)
        # remove empty strings
        pre_words = [s[0] for s in pre_res if s[0]]
        post_words = [s[0] for s in post_res if s[0]]
        pre_sym = [s[1] for s in pre_res if s[1]]
        post_sym = [s[1] for s in post_res if s[1]]

        # XXX Should be set instead?
        words = dict(
            pre=pre_words if len(pre_words) > 0 else [""],
            post=post_words if len(post_words) > 0 else [""],
        )
        symbols = dict(
            pre=pre_sym if len(pre_sym) > 0 else [""],
            post=post_sym if len(post_sym) > 0 else [""],
        )
        return words, symbols

    def to_json_object(self) -> dict:
        # Deliberately skip the RegexRule implementation of this method (we
        # don't need to include our expression, as it's static)
        return dict(
            **super(RegexRule, self).to_json_object(),
            **{
                "modulus_11": self._modulus_11,
                "ignore_irrelevant": self._ignore_irrelevant,
                "whitelist": (
                    list(self._whitelist) if
                    isinstance(self._whitelist, Iterable) else self._whitelist
                ),
                "blacklist": (
                    list(self._blacklist) if
                    isinstance(self._blacklist, Iterable) else self._whitelist
                ),
            },
        )

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj: dict):
        return CPRRule(
            modulus_11=obj.get("modulus_11", True),
            ignore_irrelevant=obj.get("ignore_irrelevant", True),
            examine_context=obj.get("examine_context", True),
            sensitivity=Sensitivity.make_from_dict(obj),
            name=obj["name"] if "name" in obj else None,
            whitelist=obj.get("whitelist", True),
            blacklist=obj.get("blacklist", True),
        )


def is_number(s: str) -> bool:
    """Return True if the string is a int/float"""

    # this is the faster than try: float or re.match
    # https://stackoverflow.com/a/23639915
    return s.replace(".", "", 1).replace(",", "", 1).isdigit()


def is_alpha_case(s: str) -> bool:
    """Return True for Magenta, magenta, MAGENTA but not MaGenTa"""

    # make sure words with hypen are accepted as long as the case is ok
    s = s.replace("-", "")
    # We could enforce s.isalpha() to prevent ma10ta, but then "nr:" would fail
    return s.istitle() or s.islower() or s.isupper()  # and s.isalpha()
