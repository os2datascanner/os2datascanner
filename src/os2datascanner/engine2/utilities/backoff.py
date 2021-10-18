from time import sleep
from random import random

import structlog

logger = structlog.get_logger(__name__)


def run_with_backoff(
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
