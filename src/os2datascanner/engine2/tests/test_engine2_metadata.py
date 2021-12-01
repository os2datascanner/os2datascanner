import os.path
import unittest

from os2datascanner.engine2.model.core import SourceManager
from os2datascanner.engine2.model.file import (
        FilesystemHandle, FilesystemSource)
from os2datascanner.engine2.model.http import (WebHandle, WebSource)
from os2datascanner.engine2.model.derived.pdf import (
        PDFPageHandle, PDFObjectHandle)
from os2datascanner.engine2.model.derived.libreoffice import (
        LibreOfficeSource, LibreOfficeObjectHandle)


test_data = FilesystemSource(os.path.join(os.path.dirname(__file__), "data"))


class MetadataTest(unittest.TestCase):
    def test_odt_extraction(self):
        handle = LibreOfficeObjectHandle(
                LibreOfficeSource(
                        FilesystemHandle(
                                test_data, "libreoffice/embedded-cpr.odt")),
                "embedded-cpr.html")
        with SourceManager() as sm:
            metadata = handle.follow(sm).get_metadata()
        self.assertEqual(
                metadata["od-creator"],
                "Alexander John Faithfull",
                "metadata extraction failed")

    def test_pdf_extraction(self):
        handle = PDFObjectHandle.make(
                FilesystemHandle(test_data, "pdf/embedded-cpr.pdf"),
                1, "page.txt")
        with SourceManager() as sm:
            metadata = handle.follow(sm).get_metadata()
        self.assertEqual(
                metadata["pdf-author"],
                "Alexander John Faithfull",
                "metadata extraction failed")

    def test_weird_pdf_metadata(self):
        """Null bytes in PDF metadata should be automatically removed."""
        handle = PDFPageHandle.make(
                FilesystemHandle(test_data, "pdf/null-byte-in-author.pdf"), 1)
        with SourceManager() as sm:
            metadata = handle.follow(sm).get_metadata()
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
