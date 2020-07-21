import os.path
import unittest

from os2datascanner.utils.metadata import guess_responsible_party
from os2datascanner.engine2.model.core import Handle, Source, SourceManager
from os2datascanner.engine2.model.file import (
        FilesystemHandle, FilesystemSource)
from os2datascanner.engine2.model.derived.libreoffice import (
        LibreOfficeObjectHandle, LibreOfficeSource)


here_path = os.path.dirname(__file__)
test_data_path = os.path.join(here_path, "data")
test_handle = LibreOfficeObjectHandle(
        LibreOfficeSource(
                FilesystemHandle(
                        FilesystemSource(test_data_path),
                        "libreoffice/embedded-cpr.odt")),
        "embedded-cpr.html")


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
    def setUp(self):
        self.handle_proxy = CountingProxy(test_handle)

    def test_odt_extraction(self):
        with SourceManager() as sm:
            metadata = guess_responsible_party(self.handle_proxy, sm)
        self.assertEqual(
                metadata["od-modifier"],
                "Alexander John Faithfull",
                "metadata extraction failed")
        self.assertEqual(
                self.handle_proxy.get_attr_access_count("follow"),
                0,
                "metadata extraction from synthetic file attempted")
