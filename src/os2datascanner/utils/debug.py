import sys
import signal
import traceback


def _backtrace(signal, frame):
    print("Got SIGUSR1, printing stacktrace:", file=sys.stderr)
    traceback.print_stack()


def register_backtrace_signal(sigid=signal.SIGUSR1):
    return signal.signal(sigid, _backtrace)


__all__ = ("register_backtrace_signal",)
