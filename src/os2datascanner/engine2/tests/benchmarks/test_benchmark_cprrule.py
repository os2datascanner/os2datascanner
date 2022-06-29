"""Benchmarking for CPRRule."""
from os2datascanner.engine2.rules.cpr import CPRRule
from .utilities import HTML_CONTENT


def test_benchmark_cpr_rule_no_context(benchmark):
    """Test performance on CPRRule without enabling examine_context."""
    content = HTML_CONTENT
    rule = CPRRule(modulus_11=True,
                   ignore_irrelevant=False,
                   examine_context=False)
    benchmark(rule.match, content)


def test_benchmark_cpr_rule_with_context(benchmark):
    """Test performance on CPRRule with examine_context enabled."""
    content = HTML_CONTENT
    rule = CPRRule(modulus_11=True,
                   ignore_irrelevant=False,
                   examine_context=True)
    benchmark(rule.match, content)
