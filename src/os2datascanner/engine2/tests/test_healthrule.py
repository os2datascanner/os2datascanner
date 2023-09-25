import unittest

from os2datascanner.engine2.rules.experimental.health_rule import TurboHealthRule


class TestTurboHealthRule(unittest.TestCase):
    def setUp(self):
        self.rule = TurboHealthRule()

    def test_health_term_in_content(self):
        """
        A basic unit test to make sure that TurboHealthRule finds
        the same matches as the new OrderedWordListRule would with
        the same dataset.
        """
        # Arrange
        content = "Cancer er en grim sygdom."
        expected = ["cancer", "sygdom"]

        # Act
        actual = list(self.rule.match(content))

        # Assert
        self.assertEqual(len(actual), len(expected))
        for i, m in enumerate(actual):
            self.assertEqual(m["match"], expected[i])
