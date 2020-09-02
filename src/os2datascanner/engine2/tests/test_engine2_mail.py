import os.path
from unittest import TestCase

from os2datascanner.engine2.model.core import Source, SourceManager
from os2datascanner.engine2.model.file import (
        FilesystemHandle, FilesystemSource)
from os2datascanner.engine2.model.derived.mail import (
        MailSource, MailPartHandle)


here_path = os.path.dirname(__file__)
test_data_path = os.path.join(here_path, "data", "mail")



class Engine2MailTest(TestCase):
    def test_eml_files(self):
        fs = FilesystemSource(test_data_path)
        with SourceManager() as sm:
            for h in fs.handles(sm):
                mail_source = Source.from_handle(h)
                self.assertIsInstance(
                        mail_source,
                        MailSource,
                        "conversion of {0} to MailSource failed".format(h))
                for h in mail_source.handles(sm):
                    self.assertIsInstance(
                            h,
                            MailPartHandle)

    def test_alternative_trimming(self):
        alternative_source = MailSource(
                FilesystemHandle.make_handle(
                        os.path.join(test_data_path, "alternative.eml")))
        with SourceManager() as sm:
            self.assertEqual(
                    len(list(alternative_source.handles(sm))),
                    1,
                    "text/plain trimming failed")
