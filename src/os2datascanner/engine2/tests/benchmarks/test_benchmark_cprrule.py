"""Benchmarking for CPRRule."""
from pathlib import Path

from os2datascanner.engine2.rules.cpr import CPRRule

DATA_ROOT = Path('/code/src/os2datascanner/engine2/tests/data/')

BIG_HTML = DATA_ROOT / 'html' / 'Midler-til-frivilligt-arbejde.html'


def read_content(path):
    """Helper function that reads some content into memory."""
    content = ""
    with path.open("r", encoding="utf-8",
                   errors="ignore") as file_pointer:
        content = file_pointer.read()

    return content


CONTENT = read_content(BIG_HTML)


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
