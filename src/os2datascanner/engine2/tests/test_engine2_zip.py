import os.path
import unittest

from os2datascanner.engine2.model.core import Source, SourceManager
from os2datascanner.engine2.model.file import (
        FilesystemSource, FilesystemHandle)
from os2datascanner.engine2.model.derived.zip import ZipSource


here_path = os.path.dirname(__file__)
test_data_path = os.path.join(here_path, "data", "zip")


class ZipTests(unittest.TestCase):
    def test_encrypted_zip(self):
        # Check that all the ZipHandles we get out of an encrypted Zip file
        # actually work. (It's fine if we don't get any, but the ones we *do*
        # need to work!)
        encrypted_file = ZipSource(
                FilesystemHandle(
                        FilesystemSource(test_data_path),
                        "encrypted-test-vector.zip"))
        with SourceManager() as sm:
            for h in encrypted_file.handles(sm):
                h.follow(sm).compute_type()
