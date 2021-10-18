import os.path
import unittest

from os2datascanner.engine2.model.core import SourceManager
from os2datascanner.engine2.model.file import (
        FilesystemHandle, FilesystemSource)
from os2datascanner.engine2.model.http import (WebHandle, WebSource)
from os2datascanner.engine2.model.derived.pdf import (
        PDFSource, PDFPageHandle, PDFPageSource, PDFObjectHandle)
from os2datascanner.engine2.model.derived.libreoffice import (
        LibreOfficeSource, LibreOfficeObjectHandle)


here_path = os.path.dirname(__file__)
test_data_path = os.path.join(here_path, "data")
odt_test_handle = LibreOfficeObjectHandle(
        LibreOfficeSource(
                FilesystemHandle(
                        FilesystemSource(test_data_path),
                        "libreoffice/embedded-cpr.odt")),
        "embedded-cpr.html")
pdf_test_handle = PDFObjectHandle(
        PDFPageSource(
                PDFPageHandle(
                        PDFSource(
                                FilesystemHandle(
                                        FilesystemSource(test_data_path),
                                        "pdf/embedded-cpr.pdf")), "1")),
        "page.txt")


class MetadataTest(unittest.TestCase):
    def test_odt_extraction(self):
        with SourceManager() as sm:
            metadata = odt_test_handle.follow(sm).get_metadata()
        self.assertEqual(
                metadata["od-creator"],
                "Alexander John Faithfull",
                "metadata extraction failed")

    def test_pdf_extraction(self):
        with SourceManager() as sm:
            metadata = pdf_test_handle.follow(sm).get_metadata()
        self.assertEqual(
                metadata["pdf-author"],
                "Alexander John Faithfull",
                "metadata extraction failed")

    def test_web_domain_extraction(self):
        with SourceManager() as sm:
            metadata = WebHandle(
                    WebSource("https://www.example.invalid./"),
                    "/cgi-bin/test.pl").follow(sm).get_metadata()
        self.assertEqual(
                metadata.get("web-domain"),
                "www.example.invalid.",
                "web domain metadata missing")
