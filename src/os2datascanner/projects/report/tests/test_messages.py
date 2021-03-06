import unittest
from datetime import datetime, timezone, timedelta


from os2datascanner.utils.system_utilities import parse_isoformat_timestamp


def seconds_to_tz(sec):
    return timezone(timedelta(seconds=sec))


class MessagesTests(unittest.TestCase):
    def test_parse_isoformat(self):
        tests = [
            ("2020-01-01T04:13:16-04:00", datetime(
                    2020, 1, 1, 4, 13, 16, tzinfo=seconds_to_tz(-14400))),
            ("2020-01-01T04:13:16-0230", datetime(
                    2020, 1, 1, 4, 13, 16, tzinfo=seconds_to_tz(-9000))),
            ("2020-01-01T04:13:16Z", datetime(
                    2020, 1, 1, 4, 13, 16, tzinfo=timezone.utc)),
            ("2020-01-01T04:13:16+0000", datetime(
                    2020, 1, 1, 4, 13, 16, tzinfo=timezone.utc)),
            ("2020-01-01T04:13:16+00:00", datetime(
                    2020, 1, 1, 4, 13, 16, tzinfo=timezone.utc)),
            ("2020-01-01T04:13:16+01:00", datetime(
                    2020, 1, 1, 4, 13, 16, tzinfo=seconds_to_tz(3600))),
            ("2020-01-01T04:13:16+0230", datetime(
                    2020, 1, 1, 4, 13, 16, tzinfo=seconds_to_tz(9000))),
            ("2020-01-01T04:13:16+04:00", datetime(
                    2020, 1, 1, 4, 13, 16, tzinfo=seconds_to_tz(14400))),
        ]
        for string, timestamp in tests:
            self.assertEqual(
                    parse_isoformat_timestamp(string),
                    timestamp,
                    "datestamp comparison failed")
