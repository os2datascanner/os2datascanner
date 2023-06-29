import unittest
import contextlib

from os2datascanner.engine2.model.core import Source, SourceManager
from os2datascanner.engine2.model.file import FilesystemSource
from os2datascanner.engine2.commands.utils import DemoSourceUtility as TestSourceUtility


class Engine2TestErrors(unittest.TestCase):
    def test_relative_filesystemsource(self):
        with self.assertRaises(ValueError):
            FilesystemSource("../../projects/admin/tests/data/")

    def test_double_mime_registration(self):
        with self.assertRaises(ValueError):
            @Source.mime_handler("application/zip")
            class Dummy:
                pass

    def test_handles_failure(self):
        with self.assertRaises(Exception) as e, SourceManager() as sm:
            source = TestSourceUtility.from_url("http://example.invalid./")
            with contextlib.closing(source.handles(sm)) as handles:
                next(handles)
        exception = e.exception
        if exception:
            print(f"got expected exception for {TestSourceUtility.to_url(source)}\n{exception}")
