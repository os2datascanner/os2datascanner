import os.path
import unittest

from os2datascanner.utils.metadata import guess_responsible_party
from os2datascanner.engine2.model.core import Handle, Source, SourceManager
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


class CountingProxy:
    def __init__(self, real_handle):
        self.__attr_accesses = {}
        self._real_handle = real_handle

    def __getattr__(self, attr):
        self.__attr_accesses[attr] = self.get_attr_access_count(attr) + 1
        return getattr(self._real_handle, attr)

    def get_attr_access_count(self, attr):
        return self.__attr_accesses.get(attr, 0)


class MetadataTest(unittest.TestCase):
    def test_odt_extraction(self):
        with SourceManager() as sm:
            metadata = guess_responsible_party(odt_test_handle, sm)
        self.assertEqual(
                metadata["od-creator"],
                "Alexander John Faithfull",
                "metadata extraction failed")

    def test_pdf_extraction(self):
        proxy = CountingProxy(pdf_test_handle)
        with SourceManager() as sm:
            metadata = guess_responsible_party(proxy, sm)
        self.assertEqual(
                metadata["pdf-author"],
                "Alexander John Faithfull",
                "metadata extraction failed")
        self.assertEqual(
                proxy.get_attr_access_count("follow"),
                0,
                "metadata extraction from synthetic file attempted")

    def test_web_domain_extraction(self):
        with SourceManager() as sm:
            metadata = guess_responsible_party(
                    WebHandle(
                            WebSource("https://www.example.com/"),
                            "/cgi-bin/test.pl"), sm)
        self.assertEqual(
                metadata.get("web-domain"),
                "www.example.com",
                "web domain metadata missing")
