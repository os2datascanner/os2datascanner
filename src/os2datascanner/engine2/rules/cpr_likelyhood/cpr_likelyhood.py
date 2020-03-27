# import time
from datetime import date


class CprLikelyhoodCalculator(object):
    """
    Implemented logic:
    * CPRs that does not contain 10 digits are considred non-cprs
    * CPRs that belong to the future are considred non-cprs
    * CPRs that does not obey mod11 is considred non-cprs, unless they correspond
      to a magic date.
    * The likelyhood of a CPR to be actually in use is calculated from its position
      in the daily list of legal CPRs, the later in the list, the less likely it
      is to be a used number.
    * Currently, if a cpr-number matches a magic date, the returned values is
      always 0.5
    """

    def __init__(self):
        # Cache of dates where the possible CPRs has already been calculated.
        self.cached_cprs = {}

        self.latest_error = ''
        self.magic_dates = []
        # Currently all dates with non-mod11 cpr's are January 1.
        for year in [1960, 1964, 1965, 1966, 1969, 1970, 1974, 1980, 1982, 1984,
                     1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992]:
            self.magic_dates.append(date(year, 1, 1))

    def _check_mod11(self, cpr: str) -> bool:
        """
        Checks if a given CPR obeys mod11.
        :param cpr: The CPR to check.
        :return: Boolean indicating if mod11 is obeyed.
        """
        mod_11_table = [4, 3, 2, 7, 6, 5, 4, 3, 2]
        mod_11_sum = 0
        for i in range(0, 9):
            mod_11_sum += int(cpr[i]) * mod_11_table[i]
        remainder = (mod_11_sum + int(cpr[9])) % 11
        return remainder == 0

    def _form_validator(self, cpr: str) -> str:
        """
        Checks a cpr number for formal validity.
        This includes checking that the cpr number consists solely of digits and that
        the length is correct.
        :param cpr: The cpr-number to check.
        :return: A string if length 0 if correct, otherwise an error description.
        """
        if len(cpr) < 10:
            return 'CPR too short'
        if len(cpr) > 10:
            return 'CPR too long'
        if not cpr.isdigit():
            return 'CPR can only contain digits'

        try:
            self._calculate_date(cpr)
        except ValueError:
            return 'Illegal date'
        return ''

    def _legal_7s(self, year: int) -> list:
        """
        Returns the possible values of CPR digit 7 for a given year.
        :param year: The year to check.
        :return: A list of legal digit 7 values.
        """
        if year < 1858:
            raise Exception('Too early for CPR')
        if 1858 <= year <= 1899:
            legal_7s = [5, 6, 7, 8]
        if 1900 <= year <= 1936:
            legal_7s = [0, 1, 2, 3]
        if 1937 <= year <= 1999:
            legal_7s = [0, 1, 2, 3, 4, 9]
        if 2000 <= year <= 2036:
            legal_7s = [4, 5, 6, 7, 8, 9]
        if 2037 <= year <= 2057:
            legal_7s = [5, 6, 7, 8]
        if year > 2057:
            raise Exception('Too late for CPR')
        return legal_7s

    def _calculate_date(self, cpr: str) -> date:
        """
        Calculates the date corresponding to a given CPR number.
        :param cpr: The CPR-number to resolve.
        :return: The actual birth date for the person, including full year.
        """
        day = cpr[0:2]
        month = cpr[2:4]
        short_year = cpr[4:6]

        if cpr[6] in ('0', '1', '2', '3'):
            full_year = '19' + short_year

        if cpr[6] == '4':
            if int(short_year) < 37:
                full_year = '20' + short_year
            else:
                full_year = '19' + short_year

        if cpr[6] in ('5', '6', '7', '8'):
            if int(short_year) < 58:
                full_year = '20' + short_year
            else:
                full_year = '18' + short_year

        if cpr[6] == '9':
            if int(short_year) < 37:
                full_year = '20' + short_year
            else:
                full_year = '19' + short_year

        birthdate = date(
            int(full_year), int(month), int(day)
        )
        return birthdate

    def _calc_all_cprs(self, birth_date: date) -> list:
        """
        Calculate all legal CPRs for a given birth date.
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
                        birth_date.strftime('%d%m%y') +
                        str(index_7) +
                        str(i).zfill(3)
                    )
                    valid = self._check_mod11(cpr_candidate)
                    if valid:
                        legal_cprs.append(cpr_candidate)

        self.cached_cprs[cache_key] = legal_cprs
        return legal_cprs

    def cpr_check(self, cpr: str) -> float:
        """
        Check a CPR number to attempt to evaluate whether it is likely
        to be a valid, used CPR number. A value of 0 means that it cannot
        be a CPR number, in that case self.lates_error is updated with a
        statement telling why it is not legal.
        If the number is syntactically correct, it is estimated whether it
        is likely to be a used number. A value of 1 does not guarantee that
        is in use, but is just used to indicate that it has the highest
        probability that can be establihed from this estimation method.
        :param cpr: The CPR number to check.
        :return: A value between 0 and 1 indicating the probability that it
        a real CPR number.
        """
        error = self._form_validator(cpr)
        if error:
            self.latest_error = error
            return 0.0

        birth_date = self._calculate_date(cpr)
        if birth_date > date.today():
            self.latest_error = 'CPR newer than today'
            return 0.0

        if not self._check_mod11(cpr):
            if birth_date not in self.magic_dates:
                self.latest_error = 'Modulus 11 does not match'
                return 0.0
            else:
                return 0.5

        legal_cprs = self._calc_all_cprs(birth_date)
        index_number = legal_cprs.index(cpr)
        self.latest_error = ''

        if index_number <= 100:
            return 1.0
        if 100 < index_number <= 200:
            return 0.8
        if 200 < index_number <= 250:
            return 0.6
        if 250 < index_number <= 350:
            return 0.25
        if index_number > 350:
            return 0.1
        raise Exception('We should not end here, index is {}'.format(index_number))


if __name__ == '__main__':
    cpr_calc = CprLikelyhoodCalculator()
    print(cpr_calc.cpr_check('1111111118'))
    print(cpr_calc.latest_error)
