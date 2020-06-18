import os.path
import unittest

from os2datascanner.engine2.model.core import Source, SourceManager
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
                yield from rule.match(representation.value)


class Engine2CompoundSourceTest(unittest.TestCase):
    def setUp(self):
        self.rule = CPRRule(modulus_11=False, ignore_irrelevant=False)

    def run_rule(self, source, sm):
        results = list(try_apply(sm, source, self.rule))
        self.assertEqual(
                results,
                [
                    {
                        "offset": 0,
                        "match": "1310XXXXXX",
                        "context": "XXXXXX-XXXX",
                        "context_offset": 0,
                        "sensitivity": None,
                        "probability": 1.0
                    }
                ])

    def run_rule_on_handle(self, handle):
        with SourceManager() as sm:
            source = Source.from_handle(handle, sm)
            self.assertIsNotNone(
                    source,
                    "{0} couldn't be made into a Source".format(handle))
            self.run_rule(source, sm)

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

    def test_doc(self):
        self.run_rule_on_handle(
                FilesystemHandle.make_handle(
                        os.path.join(
                                test_data_path,
                                "msoffice/embedded-cpr.doc")))
