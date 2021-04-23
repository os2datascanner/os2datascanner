from parameterized import parameterized

from django.core.exceptions import ValidationError
from django.test import TestCase

from os2datascanner.projects.admin.organizations.models.aliases import AliasType


class AliasTypeTest(TestCase):

    def setUp(self) -> None:
        self.test_values = {
            'valid_email': 'test@magenta.dk',
            'invalid_email': "this is not an email",
            'valid_sid': "S-1-5-21-3623811015-3361044348-30300820-1013",
            'invalid_sid': "42",
        }

    def test_member_creation(self):
        for member in AliasType:
            self.assertIsInstance(member, AliasType)
            self.assertTrue(hasattr(member, 'validator'))

    @parameterized.expand([
        ('Valid email', AliasType.EMAIL, 'valid_email'),
        ('Valid SID', AliasType.SID, 'valid_sid'),
        ('Invalid email as Generic', AliasType.GENERIC, 'invalid_email'),
        ('Invalid SID as Generic', AliasType.GENERIC, 'invalid_sid'),
    ])
    def test_validators_pass(self, _, alias_type, value_key):
        value = self.test_values[value_key]
        self.assertIsNone(alias_type.check(value))

    @parameterized.expand([
        ('Invalid email', AliasType.EMAIL, 'invalid_email'),
        ('Invalid SID', AliasType.SID, 'invalid_sid'),
    ])
    def test_validators_fail(self, _, alias_type, value_key):
        value = self.test_values[value_key]
        with self.assertRaises(ValidationError):
            alias_type.check(value)
