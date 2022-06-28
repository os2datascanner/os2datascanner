"""Benchmarking for CPRRule."""
import codecs

from os2datascanner.engine2.rules.cpr import CPRRule

CONTENT_PATH = '/code/src/os2datascanner/engine2/tests/data/html/Midler-til-frivilligt-arbejde.html'


def read_content():
    """Helper function that reads some content into memory."""
    content = ""
    with codecs.open(CONTENT_PATH, "r",
                     encoding="utf-8",
                     errors="ignore") as file_pointer:
        content = file_pointer.read()

    return content


CONTENT = read_content()


def test_benchmark_cpr_rule_no_context(benchmark):
    """Test performance on CPRRule without enabling examine_context."""
    content = CONTENT
    rule = CPRRule(modulus_11=True,
                   ignore_irrelevant=False,
                   examine_context=False)
    benchmark(rule.match, content)


def test_benchmark_cpr_rule_with_context(benchmark):
    """Test performance on CPRRule with examine_context enabled."""
    content = CONTENT
    rule = CPRRule(modulus_11=True,
                   ignore_irrelevant=False,
                   examine_context=True)
    benchmark(rule.match, content)
