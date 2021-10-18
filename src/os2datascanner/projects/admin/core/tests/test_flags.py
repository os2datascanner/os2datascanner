from parameterized import parameterized
from django.test import TestCase

from ..models import ModelChoiceEnum
from ..models import ModelChoiceFlag
from django.core.exceptions import ValidationError


class ModelChoiceFlagTest(TestCase):

    def setUp(self) -> None:
        self.enum_class = ModelChoiceFlag(
            'TestEnum', {
                'FIRST': (1, 'first label'),
                'SECOND': (2, 'second label')
            }
        )

    def test_choices(self):
        """The choices method returns expected format."""
        expected = [(1, "First label"), (2, "Second label")]
        self.assertEqual(expected, self.enum_class.choices())

    @parameterized.expand([
        ('zero-value flag', 0, []),
        ('Single value flag', 1, ['1']),
        ('Combined value flag', 3, ['1', '2']),
    ])
    def test_selected_list(self, _, flag_value, expected):
        """The selected list method returns expected values."""
        flag = self.enum_class(flag_value)
        self.assertEqual(expected, flag.selected_list)

    @parameterized.expand([
        ("Zero contains zero", 0, 0, False),
        ("Zero contains first", 0, 1, False),
        ("Single contains self", 1, 1, True),
        ("Single contains other", 1, 2, False),
        ("Single contains combination", 1, 3, False),
        ("Combination contains first", 3, 1, True),
        ("Combination contains second", 3, 2, True),
        ("Combination contains self", 3, 3, True),
        ("Combination contains zero", 3, 0, False),
    ])
    def test_contains(self, _, flag_value, test_value, expected):
        """Contains behaves as expected."""
        flag = self.enum_class(flag_value)
        test = self.enum_class(test_value)
        self.assertEqual(expected, test in flag)

    @parameterized.expand([
        ('Negative number', -1),
        ('Too high number', 0b100),
    ])
    def test_feature_validator_invalid(self, _, value):
        """Validator throws exception as expected."""
        with self.assertRaises(ValidationError):
            self.enum_class.validator(value)

    @parameterized.expand([
        ('Zero', 0),
        ('First', 1),
        ('Second', 0b10)
    ])
    def test_feature_validator_invalid(self, _, value):  # noqa: F811
        """Validator passes as expected."""
        self.enum_class.validator(value)


class ModelChoiceEnumTest(TestCase):

    def setUp(self) -> None:
        self.enum_class = ModelChoiceEnum(
            'TestEnum', {
                'FIRST': ('first', 'first label'),
                'SECOND': ('second', 'second label')
            }
        )

    def test_choices(self):
        """The choices method returns expected format."""
        expected = [('first', "First label"), ('second', "Second label")]
        self.assertEqual(expected, self.enum_class.choices())
