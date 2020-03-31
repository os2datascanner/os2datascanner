from .rule import Rule, Sensitivity
from .regex import RegexRule
from .utilities.cpr_probability import (get_birth_date, cpr_exception_dates,
        modulus11_check_raw)

cpr_regex = r"\b(\d{2}[\s]?\d{2}[\s]?\d{2})(?:[\s\-/\.]|\s\-\s)?(\d{4})\b"


class CPRRule(RegexRule):
    type_label = "cpr"

    def __init__(self, modulus_11=True,
            ignore_irrelevant=True, **super_kwargs):
        super().__init__(cpr_regex, **super_kwargs)
        self._modulus_11 = modulus_11
        self._ignore_irrelevant = ignore_irrelevant

    @property
    def presentation_raw(self):
        subdescriptor = "with "
        if self._modulus_11:
            subdescriptor += "modulus 11"
            if self._ignore_irrelevant:
                subdescriptor += " and "
        if self._ignore_irrelevant:
            subdescriptor += "relevance check"

        if subdescriptor != "with ":
            return "CPR number ({0})".format(subdescriptor)
        else:
            return "CPR number"

    def match(self, content):
        if content is None:
            return

        for m in self._compiled_expression.finditer(content):
            cpr = m.group(1).replace(" ", "") + m.group(2)
            valid_date = date_check(cpr, self._ignore_irrelevant)
            if self._modulus_11:
                try:
                    valid_modulus11 = modulus11_check(cpr)
                except ValueError:
                    valid_modulus11 = True
            else:
                valid_modulus11 = True
            cpr = cpr[0:4] + "XXXXXX"
            # Calculate context.
            low, high = m.span()
            if low < 50:
                # Sanity
                low = 50
            match_context = content[low - 50:high + 50]
            match_context = self._compiled_expression.sub(
                    "XXXXXX-XXXX", match_context)

            if valid_date and valid_modulus11:
                yield {
                    "offset": m.start(),
                    "match": cpr,
                    "context": match_context,
                    "context_offset": m.start() - (low - 50)
                }

    def to_json_object(self):
        # Deliberately skip the RegexRule implementation of this method (we
        # don't need to include our expression, as it's static)
        return dict(**super(RegexRule, self).to_json_object(), **{
            "modulus_11": self._modulus_11,
            "ignore_irrelevant": self._ignore_irrelevant
        })

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj):
        return CPRRule(modulus_11=obj["modulus_11"],
                ignore_irrelevant=obj["ignore_irrelevant"],
                sensitivity=Sensitivity.make_from_dict(obj),
                name=obj["name"] if "name" in obj else None)


def date_check(cpr, ignore_irrelevant=True):
    """Check a CPR number for a valid date.

    The CPR number is passed as a string of sequential digits with no spaces
    or dashes.
    If ignore_irrelevant is True, then CPRs with a
    7th digit of 5, 6, 7, or 8 AND year > 37 will be considered invalid.
    """
    try:
        _get_birth_date(cpr, ignore_irrelevant=ignore_irrelevant)
        return True
    except ValueError:
        # Invalid date
        return False

def modulus11_check(cpr):
    """Perform a modulo-11 check on a CPR number with exceptions.

    Return True if the number either passes the modulus-11 check OR is one
    assigned to a person born on one of the exception dates where the
    modulus-11 check should not be applied.
    """
    try:
        birth_date = _get_birth_date(cpr, ignore_irrelevant=False)
    except ValueError:
        return False

    # Return True if the birth dates are one of the exceptions to the
    # modulus 11 rule.
    if birth_date in cpr_exception_dates:
        return True
    else:
        # Otherwise, perform the modulus-11 check
        return modulus11_check_raw(cpr)
