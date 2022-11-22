import unittest

from os2datascanner.engine2.model.core import SourceManager


class Tracker:
    special_cookie = object()

    def __init__(self):
        self.count = 0

    def _generate_state(self, sm):
        self.count += 1
        try:
            yield self.special_cookie
        finally:
            self.count -= 1


class Dependent:
    def __init__(self, parent):
        self._parent = parent
        self.count = 0

    def _generate_state(self, sm):
        self.count += 1
        try:
            yield sm.open(self._parent)
        finally:
            self.count -= 1


class BrokenSource:
    def _generate_state(self, sm):
        raise ValueError("Operation failed: eth0 carrier on fire?")
        yield from []


class Engine2SourceManagerTest(unittest.TestCase):
    def test_basic(self):
        tracker = Tracker()
        with SourceManager() as sm:
            sm.open(tracker)
            sm.open(tracker)
            self.assertEqual(
                    tracker.count,
                    1,
                    "SourceManager opened the same object twice")
        self.assertEqual(
                tracker.count,
                0,
                "SourceManager didn't close the object")

    def test_dependencies(self):
        tracker1 = Tracker()
        tracker2 = Tracker()
        dependent = Dependent(tracker1)
        with SourceManager() as sm:
            sm.open(tracker1)
            sm.open(tracker2)
            sm.open(dependent)

            self.assertEqual(
                    dependent.count,
                    1,
                    "SourceManager didn't open the dependent")

            sm.close(tracker1)

            self.assertEqual(
                    dependent.count,
                    0,
                    "SourceManager didn't close the dependent")
            self.assertEqual(
                    tracker1.count,
                    0,
                    "SourceManager didn't close the parent object")
            self.assertEqual(
                    tracker2.count,
                    1,
                    "SourceManager closed an unrelated object")
        self.assertEqual(
                tracker2.count,
                0,
                "SourceManager didn't eventually close the unrelated object")

    def test_width(self):
        tracker1 = Tracker()
        tracker2 = Tracker()
        tracker3 = Tracker()
        with SourceManager(width=2) as sm:
            sm.open(tracker1)
            sm.open(tracker2)

            self.assertEqual(
                    tracker1.count,
                    1)
            self.assertEqual(
                    tracker2.count,
                    1)

            sm.open(tracker3)

            self.assertEqual(
                    tracker1.count,
                    0)
            self.assertEqual(
                    tracker3.count,
                    1)

    def test_nested_lru(self):
        tracker1 = Tracker()
        tracker2 = Tracker()
        tracker3 = Tracker()
        tracker4 = Dependent(tracker1)
        with SourceManager(width=2) as sm:
            sm.open(tracker1)
            sm.open(tracker2)
            # At this point, the SourceManager is full and tracker1 is the
            # least recently used entry, so it should be evicted next

            # Opening a dependency of tracker1 should mark it as most recently
            # used, meaning that tracker2 will be evicted when we try to open
            # something new
            sm.open(tracker4)
            sm.open(tracker3)

            self.assertEqual(
                    tracker2.count,
                    0)

    def test_dependent_clearing(self, width=None):
        tracker1 = Tracker()
        tracker1a = Dependent(tracker1)
        tracker2 = Tracker()
        tracker3 = Tracker()
        tracker3a = Dependent(tracker3)
        tracker3aa = Dependent(tracker3a)
        with SourceManager(width=width) as sm:
            sm.open(tracker1a)
            sm.open(tracker2)
            sm.open(tracker3aa)

            sm.clear_dependents()
            for indie in (tracker1, tracker2, tracker3,):
                self.assertEqual(
                        indie.count,
                        1,
                        f"independent Source {indie} was closed")
            for dependent in (tracker1a, tracker3a, tracker3aa,):
                self.assertEqual(
                        dependent.count,
                        0,
                        f"dependent Source {dependent} was not closed")

    # XXX: revisit this!
    @unittest.skip("SourceManager.width bug")
    def test_width_with_depth(self):
        self.test_dependent_clearing(width=3)

    def test_generator_exception(self):
        source = BrokenSource()
        with SourceManager() as sm:
            with self.assertRaises(ValueError):
                sm.open(source)
            self.assertFalse(
                    source in sm,
                    "_generate_state failed, but Source still open")

    def test_generator_exception2(self):
        source = BrokenSource()
        with SourceManager() as sm:
            with self.assertRaises(ValueError):
                sm.open(source)
            with self.assertRaises(ValueError):
                sm.open(source)
