import unittest
from unittest.mock import Mock

from os2datascanner.engine2.pipeline.utilities.filtering import is_handle_relevant
from os2datascanner.engine2.rules.regex import RegexRule


class FilteringRuleTests(unittest.TestCase):
    """
    Tests for the Filtering/Exclusion-rule concept.

    The point of these unittests is not to test the accuracy of
    the underlying engine rule used (we have other tests for that).
    """

    def setUp(self):
        self.rule = RegexRule('PRIVAT')

    def test_handle_with_private_matches(self):
        # Arrange
        mock_handle = Mock()
        mock_handle.__str__ = Mock(return_value='C://bruger/dokumenter/PRIVAT/hemmelig.txt')

        # Act
        actual = is_handle_relevant(mock_handle, self.rule)

        # Assert
        self.assertFalse(actual)
        mock_handle.__str__.assert_called()

    def test_handle_without_private_does_not_match(self):
        # Arrange
        mock_handle = Mock()
        mock_handle.__str__ = Mock(return_value='C://bruger/dokumenter/offentlig/griseri.txt')

        # Act
        actual = is_handle_relevant(mock_handle, self.rule)

        # Assert
        self.assertTrue(actual)
        mock_handle.__str__.assert_called()

    def test_failing_check_is_relevant_and_logs(self):
        # Arrange
        mock_handle = Mock()
        mock_handle.__str__ = Mock(return_value='C://bruger/dokumenter/offentlig/griseri.txt')

        mock_rule = Mock()
        mock_rule.try_match = Mock(side_effect=KeyError('BOOM!'))

        # Act
        actual = is_handle_relevant(mock_handle, self.rule)

        # Assert
        self.assertTrue(actual)
        mock_handle.__str__.assert_called()
