import os.path
from unittest import TestCase

from os2datascanner.engine2.model.core import Source, SourceManager
from os2datascanner.engine2.model.file import (
        FilesystemHandle, FilesystemSource)
from os2datascanner.engine2.model.derived.mail import (
        MailSource, MailPartHandle)

from os2datascanner.engine2.model.utilities.mail import decode_encoded_words


here_path = os.path.dirname(__file__)
test_data_path = os.path.join(here_path, "data", "mail")


test_subject = """SV: Ændret købsaftale på plads"""


encoded_subjects = {
    "utf-8-base64": "=?utf-8?b?U1Y6IMOGbmRyZXQga8O4YnNhZnRhbGUgcMOlIHBsYWRz?=",
    "latin-1-q": "=?iso-8859-1?q?SV=3A_=C6ndret_k=F8bsaftale_p=E5_plads?=",
    "utf-8-q-split": (
            "=?utf-8?q?SV=3A_=C3=86ndret?="
            "=?utf-8?q?_k=C3=B8bsaftale_p=C3=A5_plads?="
    ),
    "mixed-q-split": (
            "=?iso-8859-1?q?SV=3A_=C6ndret?="
            "=?utf-8?q?_k=C3=B8bsaftale_p=C3=A5_plads?=")
}


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

    def test_encoded_word_decoding(self):
        """Encoded-Word values can be decoded."""
        for sort, value in encoded_subjects.items():
            with self.subTest():
                self.assertEqual(
                        test_subject,
                        decode_encoded_words(value),
                        f"decoding {sort} failed")
