"""Benchmarking for CPRRule."""

from os2datascanner.engine2.rules.cpr import CPRRule


def test_benchmark_cpr_rule_no_context(benchmark):
    """"""
    content = ""
    rule = CPRRule(modulus_11=True,
                   ignore_irrelevant=False,
                   examine_context=False)
    benchmark(rule.match, content)


def test_benchmark_cpr_rule_with_context(benchmark):
    """"""
    content = ""
    rule = CPRRule(modulus_11=True,
                   ignore_irrelevant=False,
                   examine_context=True)
    benchmark(rule.match, content)
