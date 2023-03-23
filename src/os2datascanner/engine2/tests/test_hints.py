import unittest

from os2datascanner.engine2.model.smbc import SMBCSource, SMBCHandle


class HintTests(unittest.TestCase):
    def setUp(self):
        self._hint_dict = {
            "biscuits": "tasty",
            "pet_count": {
                "dog": 4,
                "cat": 3.14159,  # one very round cat(?)
                "gerbil": 3,
            }
        }

        self._source = SMBCSource(
                "//SERVER/Resource", "username", "topsecret", "WORKGROUP8")
        self._handle = SMBCHandle(
                self._source, "~ocument.docx", hints=self._hint_dict)

    def test_hint_serialisation(self):
        """Hints survive serialisation and deserialisation."""
        rtd_handle = SMBCHandle.from_json_object(
                self._handle.to_json_object())

        for k in self._hint_dict.keys():
            hint = self._handle.hint(k)
            self.assertIsNotNone(
                    hint,
                    "hint incorrectly stored in original object")
            self.assertEqual(
                    hint,
                    rtd_handle.hint(k),
                    "hint did not survive JSON round trip")

    def test_hint_deletion(self):
        """Hints associated with an object can be deleted."""
        self._handle.clear_hints()

        for k in self._hint_dict.keys():
            self.assertIsNone(
                    self._handle.hint(k),
                    "hint survived deletion")
