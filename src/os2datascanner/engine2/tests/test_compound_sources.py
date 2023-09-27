import os.path
import unittest

from os2datascanner.engine2.model.core import Source, SourceManager
from os2datascanner.engine2.model.derived import libreoffice
from os2datascanner.engine2.model.file import FilesystemHandle
from os2datascanner.engine2.rules.cpr import CPRRule
from os2datascanner.engine2.conversions import convert


here_path = os.path.dirname(__file__)
test_data_path = os.path.join(here_path, "data")


def try_apply(sm, source, rule):
    for handle in source.handles(sm):
        derived = Source.from_handle(handle, sm)
        if derived:
            yield from try_apply(sm, derived, rule)
        else:
            resource = handle.follow(sm)
            representation = convert(resource, rule.operates_on)
            if representation:
                yield from rule.match(representation)


class Engine2CompoundSourceTest(unittest.TestCase):
    def setUp(self):
        self.rule = CPRRule(modulus_11=False, ignore_irrelevant=False)

    def run_rule(self, source, sm, offset=0):
        """spredsheets are converted to html, which is then converted to text. The html
        conversion preserves newlines and tabs, inserted between cells. This results
        in @offset != 0

        """
        results = list(try_apply(sm, source, self.rule))
        self.assertEqual(
                results,
                [
                    {
                        "offset": offset,
                        "match": "1310XXXXXX",
                        "context": "XXXXXX-XXXX",
                        "context_offset": offset,
                        "sensitivity": None,
                        "probability": 1.0
                    }
                ])

    def run_rule_on_handle(self, handle, offset=0):
        with SourceManager() as sm:
            source = Source.from_handle(handle, sm)
            self.assertIsNotNone(
                    source,
                    "{0} couldn't be made into a Source".format(handle))
            self.run_rule(source, sm, offset)

    def test_odt(self):
        self.run_rule_on_handle(
                FilesystemHandle.make_handle(
                        os.path.join(
                                test_data_path,
                                "libreoffice/embedded-cpr.odt")))

    def test_pdf(self):
        self.run_rule_on_handle(
                FilesystemHandle.make_handle(
                        os.path.join(
                                test_data_path,
                                "pdf/embedded-cpr.pdf")))

    def test_pdf_gz(self):
        self.run_rule_on_handle(
                FilesystemHandle.make_handle(
                        os.path.join(
                                test_data_path,
                                "pdf/embedded-cpr.pdf.gz")))

    def test_doc(self):
        self.run_rule_on_handle(
                FilesystemHandle.make_handle(
                        os.path.join(
                                test_data_path,
                                "msoffice/embedded-cpr.doc")))

    def test_docx(self):
        self.run_rule_on_handle(
                FilesystemHandle.make_handle(
                        os.path.join(
                                test_data_path,
                                "msoffice/embedded-cpr.docx")))

    def test_ods(self):
        self.run_rule_on_handle(
                FilesystemHandle.make_handle(
                        os.path.join(
                                test_data_path,
                                "libreoffice/test.ods")))

    def test_ods_with_hint(self):
        self.run_rule_on_handle(
                FilesystemHandle.make_handle(
                        os.path.join(
                                test_data_path,
                                "libreoffice/test.ods"),
                        hints={
                            "some-hint": ["a", "b", "c"]
                        }))

    def test_xls(self):
        self.run_rule_on_handle(
                FilesystemHandle.make_handle(
                        os.path.join(
                                test_data_path,
                                "msoffice/test.xls")))

    def test_xlsx(self):
        self.run_rule_on_handle(
                FilesystemHandle.make_handle(
                        os.path.join(
                                test_data_path,
                                "msoffice/test.xlsx")))

    def test_corrupted_doc(self):
        corrupted_doc_handle = FilesystemHandle.make_handle(
                os.path.join(
                        test_data_path, "msoffice/corrupted/test.trunc.doc"))
        corrupted_doc = Source.from_handle(corrupted_doc_handle)
        with SourceManager() as sm, self.assertRaises(
                libreoffice.UnrecognisedFormatError):
            list(corrupted_doc.handles(sm))

    def test_libreoffice_size(self):
        large_doc_handle = FilesystemHandle.make_handle(
                os.path.join(
                        test_data_path, "libreoffice/html-explosion.ods"))
        large_doc = Source.from_handle(large_doc_handle)
        with SourceManager() as sm:
            for h in large_doc.handles(sm):
                if h.name.endswith(".html"):
                    r = h.follow(sm)
                    self.assertLess(
                            r.get_size(),
                            1048576,
                            "LibreOffice HTML output was too big")

    def test_second_sheet(self):
        self.run_rule_on_handle(
                FilesystemHandle.make_handle(
                        os.path.join(
                                test_data_path,
                                "libreoffice/two-sheets.ods")))

    def test_libreoffice_spreadsheet_support(self):
        """LibreOffice can still handle spreadsheet references, even though we
        now prefer SpreadsheetSource."""
        spreadsheet_file = FilesystemHandle.make_handle(
                os.path.join(
                        test_data_path,
                        "libreoffice/test.ods"))
        with SourceManager() as sm:
            self.run_rule(
                    libreoffice.LibreOfficeSource(spreadsheet_file),
                    sm,
                    offset=8)
