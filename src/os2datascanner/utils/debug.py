import sys
import signal
import resource
import traceback
from contextlib import contextmanager


debug_functions = []


def make_caller(functions):
    def _runner(signum, frame):
        print(
                f"Got signal {signal.Signals(signum)!r},"
                " running debug functions:", file=sys.stderr)
        print("--", file=sys.stderr)
        for function in functions:
            function(signum, frame)
            print("--", file=sys.stderr)
        print("Done running debug functions", file=sys.stderr)
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
def backtrace_dbg_func(signum, frame):
    traceback.print_stack()


# The fields in the underlying C "struct rusage" object that Python exposes
# through the resource package, with descriptive labels taken from
# https://docs.python.org/3.11/library/resource.html#resource-usage
_field_descriptions = {
    "ru_utime": "time in user mode (float seconds)",
    "ru_stime": "time in system mode (float seconds)",
    "ru_maxrss": "maximum resident set size",
    "ru_ixrss": "shared memory size",
    "ru_idrss": "unshared memory size",
    "ru_isrss": "unshared stack size",
    "ru_minflt": "page faults not requiring I/O",
    "ru_majflt": "page faults requiring I/O",
    "ru_nswap": "number of swap outs",
    "ru_inblock": "block input operations",
    "ru_oublock": "block output operations",
    "ru_msgsnd": "messages sent",
    "ru_msgrcv": "messages received",
    "ru_nsignals": "signals received",
    "ru_nvcsw": "voluntary context switches",
    "ru_nivcsw": "involuntary context switches",
}


def print_rusage(robj):
    longest = (max(len(v) for v in _field_descriptions.values()) + 1)
    for field, descr in _field_descriptions.items():
        print(
                f"{descr.rjust(longest)}:"
                f" {getattr(robj, field, None)}", file=sys.stderr)


def rusage_dbg_func(signum, frame):
    usage_info = {
        tl: resource.getrusage(getattr(resource, tl))
        for tl in ("RUSAGE_CHILDREN", "RUSAGE_SELF",)
    }
    for k, v in usage_info.items():
        print(f"{k}:", file=sys.stderr)
        print_rusage(v)


__all__ = (
        "register_debug_signal", "add_debug_function",
        "remove_debug_function", "debug_helper",

        "rusage_dbg_func")
