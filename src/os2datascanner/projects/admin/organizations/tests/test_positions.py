from django.test import TestCase
from django.utils import translation

from os2datascanner.core_organizational_structure.models.position import Role


class RoleTest(TestCase):

    def setUp(self) -> None:
        translation.activate('en')

    # Generalized version found in core application
    def test_choices(self):
        """The choices method returns the expected format."""
        expected = [
            ('employee', 'employee'),
            ('manager', 'manager'),
            ('dpo', 'data protection officer')
        ]
        self.assertEqual(expected, Role.choices)
