from time import time
import unittest

from os2datascanner.engine2.utilities.backoff import run_with_backoff


class EtiquetteBreach(Exception):
    pass


class ImpoliteClientFauxPas(EtiquetteBreach):
    pass


class ImpatientClientFauxPas(ImpoliteClientFauxPas):
    pass


class TestBackoff(unittest.TestCase):
    def setUp(self):
        self.reset_busy_time()

    def fail_unconditionally(self):
        raise EtiquetteBreach()

    def fail_if_too_busy(self):
        now = time()
        try:
            if now - self.last_call_at < 7:
                raise ImpatientClientFauxPas()
            else:
                return "Successful result"
        finally:
            self.last_call_at = now

    def reset_busy_time(self):
        self.last_call_at = time()

    def test_base_failure(self):
        with self.assertRaises(ImpatientClientFauxPas):
            self.fail_if_too_busy()

    def test_eventual_success(self):
        self.assertEqual(
                run_with_backoff(
                        self.fail_if_too_busy, ImpatientClientFauxPas)[0],
                "Successful result")

    def test_base_class_success(self):
        self.assertEqual(
                run_with_backoff(
                        self.fail_if_too_busy, EtiquetteBreach)[0],
                "Successful result")

    def test_impatient_failure1(self):
        with self.assertRaises(ImpatientClientFauxPas):
            run_with_backoff(
                    self.fail_if_too_busy, ImpatientClientFauxPas,
                    max_tries=3)

    def test_impatient_failure2(self):
        call_counter = 0
        with self.assertRaises(ImpatientClientFauxPas):

            def _try_counting():
                nonlocal call_counter
                try:
                    return self.fail_if_too_busy()
                finally:
                    call_counter += 1
            run_with_backoff(
                    _try_counting, ImpatientClientFauxPas,
                    base=0.0125)
        self.assertEqual(
                call_counter,
                10,
                "called the function too few times(?)")
