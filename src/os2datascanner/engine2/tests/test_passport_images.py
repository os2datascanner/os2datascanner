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
            "Passport number C01X00T47 (issued by DEU)",
            "Passport number L898902C3 (issued by UTO)", ]


class TestPassportImages(unittest.TestCase):
    def test_passport_images(self):
        fs = FilesystemSource(test_data_path)
        content = ""
        rule = PassportRule()
        with SourceManager() as sm:
            for h in fs.handles(sm):
                resource = h.follow(sm)
                passport = convert(resource, OutputType.MRZ)
                content += passport
        matches = rule.match(content)
        print(content)
        self.assertEqual([match["match"] for match in matches], expected)
