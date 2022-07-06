from typing import NamedTuple
import datetime
import unittest

from os2datascanner.engine2.pipeline import messages


class SampleTuple(NamedTuple):
    field1: str
    field2: int
    field3: bool
    field4: object = None

    _deep_replace = messages._deep_replace


class MessageTest(unittest.TestCase):
    def test_deep_replacement(self):
        a = SampleTuple(
                field1="Hello",
                field2=12345,
                field3=True,
                field4=SampleTuple(
                        field1="Goodbye",
                        field2=67890,
                        field3=False,
                        field4=SampleTuple(
                                field1="",
                                field2=0,
                                field3=None)))

        # Test simple replacement
        self.assertEqual(
                a._deep_replace(field1="Hi").field1,
                "Hi")
        # Test 1-level deep replacement
        self.assertEqual(
                a._deep_replace(field4__field1="Bye").field4.field1,
                "Bye")
        # Test deeper replacement
        self.assertEqual(
                a._deep_replace(
                        field4__field4__field3="FileNotFound"
                ).field4.field4.field3,
                "FileNotFound")
        # Test multiple replacements at different levels
        b = a._deep_replace(
                field1="Goddag",
                field2=7-9-13,
                field3="Sandt",
                field4__field1="Farvel",
                field4__field2=117,
                field4__field3="Falsk",
                field4__field4=None)
        self.assertEqual(
                b,
                SampleTuple(
                        field1="Goddag",
                        field2=-15,
                        field3="Sandt",
                        field4=SampleTuple(
                                field1="Farvel",
                                field2=117,
                                field3="Falsk")))

    def test_old_scan_tag_parsing(self):
        with self.subTest("scan tag from versions 3.0.0-3.3.2"):
            stf = messages.ScanTagFragment.from_json_object(
                    "2019-12-20T09:00:00+01:00")
            self.assertEqual(
                    stf.time,
                    datetime.datetime(
                            2019, 12, 20,
                            9, 0, 0,
                            tzinfo=datetime.timezone(
                                    datetime.timedelta(seconds=3600))),
                    "could not parse simple date scan tag")
        with self.subTest("scan tag from versions 3.3.3-3.6.0"):
            stf = messages.ScanTagFragment.from_json_object({
                "time": "2020-06-24T09:00:00+01:00",
                "user": "jens",
                "scanner": {
                    "pk": 10,
                    "name": "Test scanner",
                    "test": False,
                },
                "organisation": "Vejstrand Kommune"
            })
            self.assertEqual(
                    stf.organisation,
                    messages.OrganisationFragment(
                            name="Vejstrand Kommune",
                            uuid=None),
                    "could not parse simple organisation scan tag")
