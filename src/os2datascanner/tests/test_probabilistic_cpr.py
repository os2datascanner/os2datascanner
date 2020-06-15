import random
import unittest
from os2datascanner.engine2.rules.utilities.cpr_probability import (
        CprProbabilityCalculator)


def _cpr(time_from=None):
    """
    Adapted from
    https://github.com/OS2mo/os2mo-data-import-and-export/blob/development/
    os2mo_data_import/fixture_generator/dummy_data_creator.py

    Create a random valid cpr.
    :return: A valid cpr number
    """
    mod_11_table = [4, 3, 2, 7, 6, 5, 4, 3, 2]
    days_in_month = {
        '01': 31, '02': 28, '03': 31, '04': 30,
        '05': 31, '06': 30, '07': 31, '08': 31,
        '09': 30, '10': 31, '11': 30, '12': 31
    }
    days_to_choose = days_in_month.keys()
    month = list(days_to_choose)[random.randrange(0, 12)]
    day = str(random.randrange(1, 1 + days_in_month[month])).zfill(2)
    year = str(random.randrange(0, 99)).zfill(2)
    digit_7 = str(random.randrange(0, 10))

    valid_10 = False
    while not valid_10:
        digit_8_9 = str(random.randrange(10, 100))
        cpr_number = day + month + year + digit_7 + digit_8_9
        mod_11_sum = 0
        for i in range(0, 9):
            mod_11_sum += int(cpr_number[i]) * mod_11_table[i]
        remainder = mod_11_sum % 11

        if remainder == 0:
            digit_10 = '0'
        else:
            digit_10 = str(11 - remainder)
        valid_10 = (remainder is not 1)
    cpr_number = cpr_number + digit_10
    return cpr_number


class TestCprTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        pass

    def setUp(self):
        self.cpr_calc = CprProbabilityCalculator()

    def test_known_values(self):
        valid_cpr = '1111111118'
        invalid_cpr = '1111111119'

        valid_check = self.cpr_calc.cpr_check(valid_cpr)
        invalid_check = self.cpr_calc.cpr_check(invalid_cpr)
        self.assertTrue(valid_check > 0.6)
        self.assertIsInstance(invalid_check, str)

    def test_wrong_form(self):
        short_cpr = '111111111'
        long_cpr = '11111111111'

        short_check = self.cpr_calc.cpr_check(short_cpr)
        self.assertIsInstance(short_check, str)
        self.assertTrue(short_check.find('short') > 0)

        long_check = self.cpr_calc.cpr_check(long_cpr)
        self.assertIsInstance(long_check, str)
        self.assertTrue(long_check.find('long') > 0)

    def test_magic_dates(self):
        """
        This test must be updated when a more refined way of handling the magic
        dates is implemented.
        """
        magic_cpr = '0101900000'
        value = self.cpr_calc.cpr_check(magic_cpr)
        self.assertTrue(value == 0.5)

    def test_random_distribution(self):
        distribution = {}
        tests = 10000
        for i in range(0, tests):
            random_cpr = random.randrange(0, 9999999999)
            check = self.cpr_calc.cpr_check(str(random_cpr).zfill(10))
            key = check if isinstance(check, str) else 'ok'
            if key in distribution:
                distribution[key] += 1.0 / tests
            else:
                distribution[key] = 1.0 / tests

        print('Random distribution:')
        for key, value in distribution.items():
            print('{}: {:.4f}'.format(key, value))
        print('Sum: {:.4f}'.format(sum(distribution.values())))
        print()

        self.assertTrue(0.001 < distribution['ok'] < 0.005)
        self.assertTrue(0.9 < distribution['Illegal date'] < 0.999)
        self.assertTrue(0.003 < distribution['CPR newer than today'] < 0.009)
        self.assertTrue(
            0.02 < distribution['Modulus 11 does not match'] < 0.035
        )
        self.assertTrue(0.999 < sum(distribution.values()) < 1.0001)

    def test_legal_cprs(self):
        distribution = {}
        tests = 1000
        for i in range(0, tests):
            random_cpr = _cpr()
            value = self.cpr_calc.cpr_check(random_cpr)
            key = str(value)
            if key in distribution:
                distribution[key] += 1.0 / tests
            else:
                distribution[key] = 1.0 / tests

        print('Generated legal CPRs:')
        for key, value in distribution.items():
            print('{}: {:.4f}'.format(key, value))
        print('Sum: {:.4f}'.format(sum(distribution.values())))
        print()

        for key, value in distribution.items():
            if key == 0.5: # Magic value, only hit on magic dates.
                self.assertTrue(0 < value < 0.05)
            self.assertTrue(0.05 < value < 0.25)
        self.assertTrue(0.999 < sum(distribution.values()) < 1.0001)

