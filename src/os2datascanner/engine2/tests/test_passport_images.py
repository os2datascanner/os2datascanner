import os.path
import unittest

from os2datascanner.engine2.model.core import SourceManager
from os2datascanner.engine2.model.file import FilesystemSource
from os2datascanner.engine2.conversions import convert
from os2datascanner.engine2.conversions.types import OutputType
from os2datascanner.engine2.rules.passport import PassportRule

here_path = os.path.dirname(__file__)
test_data_path = os.path.join(here_path, "data", "passport")
expected = ["Passport number 000000000 (issued by DNK)",
            "Passport number C01X1626X (issued by DEU)",
            "Passport number 00000000< (issued by NOR)",
            "Passport number 59000001< (issued by SWE)", ]


class TestPassportImages(unittest.TestCase):
    fs = FilesystemSource(test_data_path)
    content = ""
    rule = PassportRule()
    with SourceManager() as sm:
        for h in fs.handles(sm):
            resource = h.follow(sm)
            passport = convert(resource, OutputType.MRZ)
            content += passport
    matches = [match["match"] for match in rule.match(content)]

    def test_all_matches_found(self):
        self.assertEqual(len(self.matches), len(expected))

    def test_correct_matches_found(self):
        self.assertTrue(all(match in expected for match in self.matches))
