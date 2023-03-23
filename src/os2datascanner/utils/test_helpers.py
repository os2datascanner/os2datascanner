from os import environ
import importlib


def in_test_environment():
    """Attempts to detect a test environment. If one is detected, the return
    value will be an object considered to be true (but will not necessarily be
    the True singleton).

    Calling this method is not usually a good idea, and callers should print a
    warning if they use it to alter their behaviour. It should normally only be
    used if performing an operation in the test enironment would have undesired
    side effects on external systems."""

    # Check whether pytest's (documented) environment variable is set
    try:
        return environ.get("PYTEST_CURRENT_TEST", None)
    except KeyError:
        pass

    # Check whether or not django.test.utils.setup_test_environment has been
    # called by checking whether its state stash object exists. This is an
    # implementation detail of Django, but has been present since 2016
    try:
        dtu = importlib.import_module("django.test.utils")
        return getattr(dtu._TestState, "saved_data", None)
    except ImportError:
        pass

    return None


__all__ = ("in_test_environment",)
