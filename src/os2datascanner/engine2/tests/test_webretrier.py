import unittest
from unittest.mock import Mock
import requests

from os2datascanner.engine2.utilities.backoff import WebRetrier
from parameterized import parameterized


class TestWebRetrier(unittest.TestCase):
    Retry_Codes = WebRetrier.RETRY_CODES

    def setUp(self):
        self.retrier = WebRetrier()

    @parameterized.expand([(code,) for code in Retry_Codes])
    def test_should_retry(self, value):
        """Provided one of WebRetrier's RETRY_CODES, should_retry should return True."""
        ex = requests.exceptions.HTTPError(
            response=Mock(status_code=value),
            request=Mock()
        )
        self.assertTrue(self.retrier._should_retry(ex),
                        f"status code {value} should have triggered a retry")

    def test_should_not_retry(self):
        """Provided an HTTP code that is not a part of WebRetrier's RETRY_CODES, should_not_retry should
        return False."""
        ex = requests.exceptions.HTTPError(
            response=Mock(status_code=100),
            request=Mock()
        )
        self.assertFalse(self.retrier._should_retry(ex))

    def test_test_return_value_with_retry_code(self):
        """Provided on of WebRetrier's RETRY_CODES, raises an HTTP error exception as
        expected and passes."""
        response = requests.Response()
        response.status_code = 503
        with self.assertRaises(requests.exceptions.HTTPError):
            self.retrier._test_return_value(response)

    def test_test_return_value_with_response(self):
        """Successful HTTP responses are not treated as back-off errors."""
        response = requests.Response()
        response.status_code = 200
        try:
            self.retrier._test_return_value(response)
        except requests.exceptions.HTTPError:
            self.fail("a successful HTTP response was treated as an error")
