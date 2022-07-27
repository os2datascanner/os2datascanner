import unittest

from os2datascanner.engine2.conversions.utilities import navigable


class Dummy:
    pass


class Dummy2:
    def __init__(self, dummy=None):
        pass


class Dummy3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


values = (
        "string value", 0.123456, 20, {"nested": "dictionary"}, [1, 5, 7, 9],
        (1, 5, 7, 10), {1, 5, 8, 7})


class NavigableTest(unittest.TestCase):
    def test_promotion(self):
        """Basic Python values can be promoted to navigable ones while
        preserving their original type."""
        for k in values:
            navi = navigable.make_navigable(k)
            self.assertEqual(
                    navi,
                    k,
                    "value did not survive promotion")
            self.assertIsInstance(
                    navi,
                    type(k),
                    "type has changed too much")
            self.assertTrue(
                    hasattr(navi, "parent"),
                    "parent attribute is missing")
            self.assertIsInstance(
                    navi,
                    navigable._NavigableBase,
                    "type is not navigable")

    def test_linked_promotion(self):
        """The parent of a navigable value is tracked."""
        parent = {}
        parent["k"] = navigable.make_navigable(1, parent=parent)
        self.assertIs(
                parent,
                parent["k"].parent,
                "navigable has the wrong parent")

    def test_bulk_promotion(self):
        """The values of a dict can be converted to navigable ones."""
        mapped_values = {type(value).__name__: value for value in values}
        navi = navigable.make_values_navigable(mapped_values)
        for v in navi.values():
            self.assertIs(
                    navi,
                    v.parent,
                    "navigable has the wrong parent")

    def test_failed_promotion(self):
        """A value with no corresponding navigable type cannot be made
        navigable."""
        with self.assertRaises(TypeError):
            navigable.make_navigable(Dummy())

    def test_promotion_registration(self):
        """New types can be made navigable."""
        navigable.make_navigable_type(Dummy2)
        dummy = navigable.make_navigable(Dummy2())
        self.assertIsInstance(
                dummy,
                navigable._NavigableBase,
                "type is not navigable")

    def test_adapter_registration(self):
        """Types without a one-argument copy constructor can also be made
        navigable by providing an adaptor function."""
        navigable.make_navigable_type(
                Dummy3, adaptor=lambda dummy: (dummy.x, dummy.y, dummy.z))
        dummy = Dummy3(5, 10, 20)
        navigable_dummy = navigable.make_navigable(dummy)
        self.assertEqual(
                (dummy.x, dummy.y, dummy.z),
                (navigable_dummy.x, navigable_dummy.y, navigable_dummy.z),
                "adaptor failed")
