import os.path
import unittest

from os2datascanner.engine2.model.core import SourceManager
from os2datascanner.engine2.model.file import FilesystemHandle


here_path = os.path.dirname(__file__)
doc_handle = FilesystemHandle.make_handle(
        os.path.join(
                here_path, "data", "msoffice", "test.doc"))
docx_handle = FilesystemHandle.make_handle(
        os.path.join(
                here_path, "data", "msoffice", "test.docx"))


class Engine2MIMETests(unittest.TestCase):
    def test_doc_mime(self):
        self.assertEqual(
                doc_handle.guess_type(),
                "application/msword",
                ".doc MIME guess is incorrect")
        with SourceManager() as sm:
            self.assertEqual(
                    doc_handle.follow(sm).compute_type(),
                    "application/msword",
                    ".doc MIME computation is incorrect")

    def test_docx_mime(self):
        self.assertEqual(
                docx_handle.guess_type(),
                "application/vnd.openxmlformats-officedocument"
                        ".wordprocessingml.document",
                ".docx MIME guess is incorrect")
        with SourceManager() as sm:
            self.assertEqual(
                    docx_handle.follow(sm).compute_type(),
                    "application/vnd.openxmlformats-officedocument"
                            ".wordprocessingml.document",
                    ".docx MIME computation is incorrect")
