"""
Unit test for the timeout module which is part of engine2's utilities.
"""
import time
import unittest
from os2datascanner.engine2.utilities.timeout import (run_with_timeout,
                                                      yield_from_with_timeout,
                                                      _signal_timeout_handler,
                                                      SignalAlarmException,
                                                      _timeout)


class TestTimeout(unittest.TestCase):
    """
    Test case class for engine2.utilities.timeout module.
    """

    # SECTION: _signal_timeout_handler

    def test_signal_timeout_handler_raises_exception(self):
        with self.assertRaises(SignalAlarmException):
            _signal_timeout_handler(None, None)

    # END

    # SECTION: _timeout

    def test_timeout_raises_sends_signal_when_expired(self):
        with self.assertRaises(SignalAlarmException):
            with _timeout(1):
                time.sleep(2)

    def test_timeout_cancels_alarm_in_due_time(self):
        result = 0
        with _timeout(2):
            result += 1

        self.assertEqual(1, result)

    def test_timeout_raises_sends_signal_for_generators(self):
        def generator():
            for num in [1, 2, 3]:
                with _timeout(1):
                    time.sleep(2)
                    yield num

        with self.assertRaises(SignalAlarmException):
            list(generator())

    # END

    # SECTION: run_with_default_timeout

    def test_run_with_timeout_no_args_no_return_finishes_in_time(self):
        (_, result) = run_with_timeout(2, lambda: time.sleep(1))
        self.assertEqual(None, result)

    def test_run_with_timeout_no_args_finishes_in_one_second(self):
        time_start = time.perf_counter()

        (finished, _) = run_with_timeout(2, lambda: time.sleep(1))

        time_elapsed = time.perf_counter() - time_start
        self.assertEqual(1, round(time_elapsed))
        self.assertTrue(finished)

    def test_run_with_timeout_no_args_retval_finishes_in_time(self):
        def func():
            time.sleep(1)
            return 1

        (finished, result) = run_with_timeout(2, func)

        self.assertTrue(finished)
        self.assertEqual(1, result)

    def test_run_with_timeout_one_arg_retval_finishes_in_time(self):
        def func(seconds):
            time.sleep(seconds)
            return seconds

        seconds = 1

        (finished, result) = run_with_timeout(2, func, seconds)

        self.assertEqual(seconds, result)
        self.assertTrue(finished)

    def test_run_with_timeout_multiple_args_retval_finishes_in_time(self):
        def func(fst, snd):
            time.sleep(fst)
            return snd

        seconds = 1

        (finished, result) = run_with_timeout(2, func, seconds, seconds)

        self.assertEqual(seconds, result)
        self.assertTrue(finished)

    def test_run_with_timeout_with_generator(self):
        def func(elements):
            for element in elements:
                yield element*2

        elements = [1, 2]

        (finished, result) = run_with_timeout(1, func, elements)

        self.assertEqual([2, 4], list(result))
        self.assertTrue(finished)

    def test_run_with_timeout_return_generator(self):
        def func(elements):
            for element in elements:
                yield element*2

        def generator():
            elements = [1, 2]
            (_, result) = run_with_timeout(1, func, elements)
            yield from result

        actual = generator()

        self.assertEqual([2, 4], list(actual))

    def test_run_with_timeout_no_args_no_return_raises_exception(self):
        time_start = time.perf_counter()

        (finished, _) = run_with_timeout(1, lambda: time.sleep(2))

        time_elapsed = time.perf_counter() - time_start
        self.assertEqual(1, round(time_elapsed))
        self.assertFalse(finished)

    def test_run_with_timeout_raises_exception_when_time_is_zero(self):
        with self.assertRaises(ValueError):
            run_with_timeout(0, lambda: time.sleep(1))

    def test_run_with_timeout_raises_exception_when_time_is_negative(self):
        with self.assertRaises(ValueError):
            run_with_timeout(-1, lambda: time.sleep(1))

    def test_run_with_timeout_raises_exception_when_time_is_none(self):
        with self.assertRaises(ValueError):
            run_with_timeout(None, lambda: time.sleep(1))

    def test_run_with_timeout_raises_exception_when_time_is_invalid_type(self):
        with self.assertRaises(TypeError):
            run_with_timeout("", lambda: time.sleep(1))

    # END

    # SECTION: yield_from_with_timeout

    def test_yield_from_with_timeout_succeeds_within_time_limit(self):
        def func(elements):
            for element in elements:
                time.sleep(1)
                yield element*2

        elements = [1, 2]

        result = list(yield_from_with_timeout(2, func(elements)))

        self.assertEqual([2, 4], result)

    def test_yield_from_with_timeout_produces_half_of_the_results(self):
        def func(elements):
            for element in elements:
                time.sleep(element)
                yield element*2

        elements = [1, 2]

        result = list(yield_from_with_timeout(2, func(elements)))

        self.assertEqual([2], result)

    def test_yield_from_with_timeout_generates_nothing_in_edge_case(self):
        def func(elements):
            for element in elements:
                time.sleep(1)
                yield element*2

        elements = [1, 2]

        result = list(yield_from_with_timeout(1, func(elements)))

        self.assertEqual([], result)

    def test_yield_from_with_timeout_generated_nothing_on_timeout(self):
        def func(elements):
            for element in elements:
                time.sleep(2)
                yield element*2

        elements = [1, 2]

        result = list(yield_from_with_timeout(1, func(elements)))

        self.assertEqual([], result)

    def test_yield_with_timeout_raises_exception_when_time_is_zero(self):
        def func(elements):
            for element in elements:
                time.sleep(2)
                yield element*2

        elements = [1, 2]

        with self.assertRaises(ValueError):
            run_with_timeout(0, func(elements))

    def test_yield_with_timeout_raises_exception_when_time_is_negative(self):
        def func(elements):
            for element in elements:
                time.sleep(2)
                yield element*2

        elements = [1, 2]

        with self.assertRaises(ValueError):
            run_with_timeout(-1, func(elements))

    def test_yield_with_timeout_raises_exception_when_time_is_none(self):
        def func(elements):
            for element in elements:
                time.sleep(2)
                yield element*2

        elements = [1, 2]

        with self.assertRaises(ValueError):
            run_with_timeout(None, func(elements))

    def test_yield_with_timeout_raises_exception_when_time_is_invalid_type(self):
        def func(elements):
            for element in elements:
                time.sleep(2)
                yield element*2

        elements = [1, 2]

        with self.assertRaises(TypeError):
            run_with_timeout("", func(elements))

    # END
