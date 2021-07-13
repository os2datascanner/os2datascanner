# import time
from typing import Union, Tuple
from datetime import date

# Updated list of dates with CPR numbers violating the Modulo-11 check. (Last
# synchronised with the CPR Office's list on January 28, 2021.)
# Source: https://cpr.dk/cpr-systemet/personnumre-uden-kontrolciffer-modulus-11-kontrol/
CPR_EXCEPTION_DATES = {
    date(1960, 1, 1),
    date(1964, 1, 1),
    date(1965, 1, 1),
    date(1966, 1, 1),
    date(1969, 1, 1),
    date(1970, 1, 1),
    date(1974, 1, 1),
    date(1980, 1, 1),
    date(1982, 1, 1),
    date(1984, 1, 1),
    date(1985, 1, 1),
    date(1986, 1, 1),
    date(1987, 1, 1),
    date(1988, 1, 1),
    date(1989, 1, 1),
    date(1990, 1, 1),
    date(1991, 1, 1),
    date(1992, 1, 1),
    date(1995, 1, 1),
}

THIS_YEAR = date.today().year


def get_birth_date(cpr: str) -> date:
    """Get the birth date as a datetime from the CPR number.

    If the CPR has an invalid birthday, raises ValueError.
    """
    day = int(cpr[0:2])
    month = int(cpr[2:4])
    year = int(cpr[4:6])

    year_check = int(cpr[6])

    # Convert 2-digit year to 4-digit:
    if year_check >= 0 and year_check <= 3:  # in (0,1,2,3)
        year += 1900
    elif year_check == 4:
        if year > 36:
            year += 1900
        else:
            year += 2000
    elif year_check >= 5 and year_check <= 8:  # in (5,6,7,8)
        if year > 57:
            year += 1800
        else:
            year += 2000
    elif year_check == 9:
        if year > 37:
            year += 1900
        else:
            year += 2000

    return date(day=day, month=month, year=year)


_mod_11_table = [4, 3, 2, 7, 6, 5, 4, 3, 2, 1]


def modulus11_check(cpr: str) -> Tuple[bool, str]:
    """Perform a modulo-11 check on a CPR number with exceptions.

    Return True if the number either passes the modulus-11 check OR is one
    assigned to a person born on one of the exception dates where the
    modulus-11 check should not be applied.
    """
    try:
        birth_date = get_birth_date(cpr)
        # IndexError if cpr is less than 7 chars
    except (ValueError, IndexError):
        return (False, "malformed birth_date")

    # Return True if the birth dates are one of the exceptions to the
    # modulus 11 rule.
    if birth_date in CPR_EXCEPTION_DATES:
        return (True, "in exception_date")
    else:
        # Otherwise, perform the modulus-11 check
        return (modulus11_check_raw(cpr), "due to modulus11")


def modulus11_check_raw(cpr: str) -> bool:
    """Perform a modulus-11 check on the CPR number.

    This should not be called directly as it does not make any exceptions
    for numbers for which the modulus-11 check should not be performed.
    """
    return sum([int(c) * v for c, v in zip(cpr, _mod_11_table)]) % 11 == 0

class CprProbabilityCalculator(object):
    """Calculate the probability that a matched str of numbers is actually a CPR

    Implemented logic:
    * CPRs that does not contain 10 digits are considred non-cprs
    * CPRs that belong to the future are considred non-cprs
    * CPRs that does not obey mod11 is considred non-cprs, unless they correspond
      to a magic date.
    * The probability of a CPR to be actually in use is calculated from its position
      in the daily list of legal CPRs, the later in the list, the less likely it
      is to be a used number.
    * Currently, if a cpr-number matches a magic date, the returned values is
      always 0.5
    """

    def __init__(self):
        # Cache of dates where the possible CPRs has already been calculated.
        self.cached_cprs = {}

    @staticmethod
    def _form_validator(cpr: str) -> str:
        """Checks a CPR number for formal validity.

        This includes checking that the cpr number consists solely of digits and that
        the length is correct.
        :param cpr: The cpr-number to check.
        :return: A string if length 0 if correct, otherwise an error description.

        """
        if len(cpr) < 10:
            return "CPR too short"
        if len(cpr) > 10:
            return "CPR too long"
        if not cpr.isdigit():
            return "CPR can only contain digits"

        try:
            get_birth_date(cpr)
        except ValueError:
            return "Illegal date"
        return ""

    @staticmethod
    def _legal_7s(year: int) -> list:
        """Returns the possible values of CPR digit 7 for a given year.

        :param year: The year to check.
        :return: A list of legal digit 7 values.
        """
        legal_7s = []
        if 1858 <= year <= 1899:
            legal_7s = [5, 6, 7, 8]
        elif 1900 <= year <= 1936:
            legal_7s = [0, 1, 2, 3]
        elif 1937 <= year <= 1999:
            legal_7s = [0, 1, 2, 3, 4, 9]
        elif 2000 <= year <= 2036:
            legal_7s = [4, 5, 6, 7, 8, 9]
        elif 2037 <= year <= 2057:
            legal_7s = [5, 6, 7, 8]
        return legal_7s

    def _calc_all_cprs(self, birth_date: date) -> list:
        """Calculate all valid CPRs for a given birth date.

        :param birh_date: The birh date to check.
        :return: A list of all legal CPRs for that date.
        """
        cache_key = str(birth_date)
        if cache_key in self.cached_cprs:
            return self.cached_cprs[cache_key]
        legal_7 = self._legal_7s(birth_date.year)

        legal_cprs = []
        for index_7 in legal_7:
            for i in range(0, 1000):
                cpr_candidate = (
                    birth_date.strftime("%d%m%y")
                    + str(index_7)
                    + str(i).zfill(3)
                )
                valid = modulus11_check_raw(cpr_candidate)
                if valid:
                    legal_cprs.append(cpr_candidate)

        self.cached_cprs[cache_key] = legal_cprs
        return legal_cprs

    def cpr_check(self, cpr: str, do_mod11_check = True) -> Union[str, float]:
        """Estimate a probality that the number is actually a CPR.

        The probability is estimated by calculating all possible CPR
        numbers's(ie. the last four digits) for the given CPR date. The CPR's of
        a given day are given by sequence, ie. the higher the potential CPR
        places in the sequence, the lower the probabilty.

        The sequence is dvivided into five slots, where the boundary is the index
        in the sequence
        [ p=1 <= 100 < p=0.8 <= 200 < p=0.6 <= 250 < p=0.25 <= 350 < p=0.1 ]

        A probability of 1 does not guarantee that the CPR is in use. It shows
        that it is among the first 100 of the sequence and thus have the highest
        probability estimated from this method.

        Note that some CPRs from 1st of Januar certain years does not validate
        the modulus 11 check. If this is the case, a probality of `p=0.5` is
        returned

        :param cpr: The CPR number to check.
        :return: A value between 0 and 1 indicating the probability that it
        is a real CPR number, or an error string if it cannot be.

        """
        error = self._form_validator(cpr)
        if error:
            return error

        birth_date = get_birth_date(cpr)
        if birth_date > date.today():
            return "CPR newer than today"

        if do_mod11_check and not modulus11_check_raw(cpr):
            if birth_date not in CPR_EXCEPTION_DATES:
                return "Modulus 11 does not match"
            else:
                return 0.5

        legal_cprs = self._calc_all_cprs(birth_date)
        index_number = legal_cprs.index(cpr)

        if index_number <= 100:
            return 1.0
        elif 100 < index_number <= 200:
            return 0.8
        elif 200 < index_number <= 250:
            return 0.6
        elif 250 < index_number <= 350:
            return 0.25
        else:
            return 0.1


if __name__ == "__main__":
    cpr_calc = CprProbabilityCalculator()
    print(cpr_calc.cpr_check("1111111118"))
