from time import sleep
from random import random

import structlog

logger = structlog.get_logger(__name__)


class Retrier:
    """A Retrier is a helper object used to repeat certain operations when a
    transient exception is raised. A concrete instance of Retrier or of one of
    its subclasses is a stateful object representing a strategy for repeat
    execution."""
    def __init__(self, *exception_set: Exception):
        self._exception_set = tuple(exception_set)

    @property
    def _should_proceed(self):
        """Indicates whether or not the state of this Retrier indicates that
        another attempt should be made."""
        return True

    def _should_retry(self, ex: Exception) -> bool:
        """Examines an exception to determine whether or not it represents a
        transient error."""
        return isinstance(ex, self._exception_set)

    def _before_retry(self, ex: Exception, op):
        """Called after _should_retry has indicated that an exception is
        transient, but before _should_proceed has been called for the next
        attempt. (The operation being executed is made available for the sake
        of debug logging.)

        This is the main hook method of the Retrier class. Subclasses might
        want to extend it to update internal state or to insert a delay."""
        pass

    def run(self, operation, *args, **kwargs):
        """Repeatedly calls operation(*args, **kwargs) until it returns without
        raising a transient error. Returns whatever that function eventually
        returns.

        Subclasses may wish to extend this method to, for example, reset parts
        of their internal state before calling this implementation."""
        while self._should_proceed:
            try:
                return operation(*args, **kwargs)
            except Exception as ex:
                if self._should_retry(ex):
                    self._before_retry(ex, operation)
                    if self._should_proceed:
                        continue
                raise

    def bind(self, operation):
        def _bind(*args, **kwargs):
            return self.run(operation, *args, **kwargs)
        return _bind


class CountingRetrier(Retrier):
    """A CountingRetrier tracks the number of attempts made to call an
    operation, and gives up after a certain number."""
    def __init__(self, *exception_set, max_tries=10, warn_after=6, **kwargs):
        super().__init__(*exception_set, **kwargs)
        self._tries = 0
        self._warn_after = warn_after
        self._max_tries = max_tries

    @property
    def _should_proceed(self):
        return self._max_tries is None or self._tries < self._max_tries

    def _before_retry(self, ex, op):
        self._tries += 1
        if self._warn_after is not None and self._tries >= self._warn_after:
            logger.info(
                "backoff failed, delaying",
                op=str(op),
                iterations=self._tries
            )

    def run(self, operation, *args, **kwargs):
        self._tries = 0
        return super().run(operation, *args, **kwargs)


class SleepingRetrier(CountingRetrier):
    """A SleepingRetrier is a CountingRetrier that also adds a delay after
    each attempt. (This is by default a static delay of one second, but
    subclasses can specify something more sophisticated by overriding the
    _compute_delay method.)"""

    def _compute_delay(self):
        return 1.0

    def _before_retry(self, ex, op):
        super()._before_retry(ex, op)
        # Only bother delaying if there's going to *be* a next attempt
        if self._should_proceed:
            sleep(self._compute_delay())


class ExponentialBackoffRetrier(SleepingRetrier):
    def __init__(self, *exception_set, base=1, ceiling=7, fuzz=0.2, **kwargs):
        super().__init__(*exception_set, **kwargs)
        self._base = base
        self._fuzz = 0
        self._ceiling = ceiling

    def _compute_delay(self):
        max_delay = self._base * (2 ** min(self._tries, self._ceiling) - 1)
        if self._fuzz:
            fuzz_diff = (max_delay * self._fuzz)
            adj = -fuzz_diff + (2 * random() * fuzz_diff)
            max_delay += adj
        return max_delay


DefaultRetrier = ExponentialBackoffRetrier
"""DefaultRetrier is an alias for whichever Retrier the project considers to be
the best choice at any given point. If you just want to retry a function a
reasonable number of times with sensible default behaviour and don't need any
particular tuning parameters, then instantiate one of these."""


def run_with_backoff(  # noqa: CCR001, too high cognitive complexity
        op, *exception_set,
        count=0, max_tries=10, ceiling=7, base=1, warn_after=6, fuzz=0):
    """Performs an operation until it succeeds (or until the maximum number of
    attempts is hit), with exponential backoff time after each failure.

    On success, returns a (result, parameters) pair; expanding the parameters
    dictionary and giving it to this function will allow the backoff behaviour
    to be persistent.

    The initial waiting period, in seconds, is given by @base. The waiting
    period is doubled after each subsequent failure, up to a threshold given
    by 2 ^ (@ceiling - 1) seconds. @count specifies the number of times the
    function has already failed for the purposes of computing the waiting
    period.

    Each failure after the @warn_after'th will print a diagnostic message to
    standard error. After @max_tries failures, the underlying exception will be
    raised to the caller (this is unaffected by @count).

    The waiting period can be randomised by setting @fuzz to a value between
    0.0 (the waiting period remains unchanged) and 1.0 (the waiting period may
    vary up or down by 100% from its computed value)."""
    count = max(0, int(count))
    base = max(0.01, base)
    end = count + max_tries
    fuzz = max(min(fuzz or 0, 1), 0)
    while count < end:
        if count:
            max_delay = base * (2 ** (min(count, ceiling) - 1))
            if fuzz:
                # Sleep time is randomly adjusted by the proportion given in
                # the fuzz parameter (0 - 0% adjustment, 1 - ±100% adjustment)
                fuzz_diff = (max_delay * fuzz)
                adj = -fuzz_diff + (2 * random() * fuzz_diff)
                max_delay += adj
            sleep(max_delay)
        try:
            return (op(), dict(
                    count=count, max_tries=max_tries, ceiling=ceiling,
                    base=base, fuzz=fuzz))
        except Exception as e:
            if isinstance(e, exception_set):
                # This exception indicates that we should back off and try
                # again
                count += 1
                if count == max_tries:
                    # ... but we've exhausted our maximum attempts
                    if warn_after and count >= warn_after:
                        logger.warning(
                            "backoff failed, giving up",
                            op=str(op),
                            iterations=count,
                        )
                    raise
                elif warn_after and count >= warn_after:
                    max_delay = base * (2 ** (min(count, ceiling) - 1))
                    logger.info(
                        "backoff failed, delaying",
                        op=str(op),
                        iterations=count,
                        between=(max_delay, max_delay * fuzz),
                    )
            else:
                # This is not a backoff exception -- raise it immediately
                raise
