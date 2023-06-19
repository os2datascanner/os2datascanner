from django.test import TestCase
from parameterized import parameterized
from ..models.organization import replace_nordics


class ReplaceSpecialCharactersTest(TestCase):
    @parameterized.expand([
        ("tæstcåsø", "t&aelig;stc&aring;s&oslash;"),
        ("Næstved", "N&aelig;stved"),
        ("Torben", "Torben"),
        ("bLaNdInG", "bLaNdInG"),
        ("BlÆnDiNg", "Bl&AElig;nDiNg"),
        ("HÅR", "H&Aring;R"),
        ("SØVAND", "S&Oslash;VAND")
    ])
    def test_nordics_are_replaced(self, input, expected):
        """
        A string containing 'æ', 'ø' and/or 'å' will have those
        instances replaced according to
        https://www.thesauruslex.com/typo/eng/enghtml.htm
        """
        replaced_string = replace_nordics(input)
        self.assertEqual(replaced_string, expected)
