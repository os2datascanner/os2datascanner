import sys
import signal
import traceback
from contextlib import contextmanager


debug_functions = []


def make_caller(functions):
    def _runner(*args, **kwargs):
        for function in functions:
            function(*args, **kwargs)
    return _runner


_call_debug_functions = make_caller(debug_functions)


def register_debug_signal(sigid=signal.SIGUSR1):
    """Registers the specified signal as the debug signal. Whenever the debug
    signal is raised, all debug functions will be called in the order in which
    they were added. (By default, the only debug function prints a stack trace
    to standard error.)"""
    return signal.signal(sigid, _call_debug_functions)


def add_debug_function(func):
    """Adds a function to the list of debug functions to be called when the
    debug signal is raised. (This function can also be used as a decorator.)

    Debug functions are invoked by a Python signal handler, and are given its
    arguments, the first of which is the signal number of the debug signal and
    the second of which is an opaque frame object."""
    debug_functions.append(func)
    return func


def remove_debug_function(func):
    """Removes a function from the list of debug functions.

    The given function must be the most recently registered debug function. If
    this is not the case, an exception will be raised."""
    if not debug_functions[-1] == func:
        raise ValueError(
                f"{func} was not the most recently"
                " registered backtrace function")
    else:
        debug_functions.pop()


@contextmanager
def debug_helper(func):
    """For the life of this context, registers the given function as a debug
    function to be called when this process receives the debug signal.

    To register debug functions more permanently, use the add_debug_function
    function."""
    try:
        add_debug_function(func)
        yield
    finally:
        remove_debug_function(func)


@add_debug_function
def _backtrace(signal, frame):
    print("Got SIGUSR1, printing stacktrace:", file=sys.stderr)
    traceback.print_stack()


__all__ = (
        "register_debug_signal", "add_debug_function",
        "remove_debug_function", "debug_helper",)
