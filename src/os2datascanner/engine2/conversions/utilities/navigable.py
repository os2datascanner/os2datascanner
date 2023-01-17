"""Navigable subclasses of various common Python types.

The Beautiful Soup library has a convenient abstraction called NavigableString
that lets strings from HTML elements carry around a reference to their element
(https://www.crummy.com/software/BeautifulSoup/bs4/doc/#navigablestring). This
module is a generalisation of that idea designed to support the efficient
execution of OS2datascanner rules: if an API call returns twenty values when
you only asked for one, why not make it possible to get the other nineteen too?

    >>> size = resource.get_size()
    >>> size
    108
    >>> isinstance(size, int)
    True
    >>> size.parent
    {'st_mode': 33188, 'st_ino': 1579180, 'st_dev': 64769, ...}
"""


import datetime

import exchangelib


class _NavigableBase:
    @classmethod
    def _real_type(cls):
        """Returns the first type in the method resolution order of the given
        class that isn't a subclass of _NavigableBase."""
        for c in cls.__mro__:
            if not issubclass(c, _NavigableBase):
                return c
        # can't happen
        return cls

    @property
    def parent(self) -> dict:
        return self._parent

    @staticmethod
    def __new__(cls, *args, **kwargs):
        constructor = cls._real_type().__new__
        if constructor != object.__new__:
            new_object = constructor(cls, *args, **kwargs)
        else:
            # object.__new__ doesn't take any arguments, even if the __init__
            # method of the class does
            new_object = constructor(cls)
        new_object._parent = None
        return new_object


_navigable_types = {}


def make_navigable_type(t, *, create=True, adaptor=None):
    """Returns a navigable subtype of the given type, optionally creating one
    if necessary. An instance of a navigable subtype has a .parent property
    that gives access to "related" values (for example, ones returned by the
    same API call).

    Navigable subtypes assume by default that their parent has a copy
    constructor (that is, that type(k)(k) returns a meaningful instance of
    type(k)). If this isn't the case, then specify an adaptor function that
    expands an object to the appropriate constructor parameters."""
    if t not in _navigable_types:
        tn = f"Navigable{t.__name__.title()}"
        if not create:
            raise TypeError(
                    f"counterpart {tn} is not defined and"
                    " will not be created")
        new_type = type(tn, (_NavigableBase, t,), {})
        if adaptor is None:
            _navigable_types[t] = new_type
        else:
            _navigable_types[t] = lambda v: new_type(*(adaptor(v)))
    return _navigable_types[t]


for t in (
        int, float, complex, list, tuple, str, bytes, bytearray, set,
        frozenset, dict,):
    make_navigable_type(t)


# Python doesn't allow these built-in types to be subclassed, so we can't make
# them navigable. Provided that we don't actually try to return them as focused
# values, it still makes sense to be able to find them through traversal
for t in (bool, range, memoryview,):
    _navigable_types[t] = t
_navigable_types[type(None)] = lambda v: None


for klass in (datetime.datetime, exchangelib.EWSDateTime):
    make_navigable_type(
            klass,
            adaptor=lambda dt: (
                    dt.year, dt.month, dt.day,
                    dt.hour, dt.minute, dt.second, dt.microsecond,
                    dt.tzinfo))


def make_navigable(v, *, parent=None):
    """Returns a navigable version of a given object under a given parent.
    (Note that the return value isn't automatically inserted into the parent
    by this function.)"""
    rv = make_navigable_type(type(v), create=False)(v)
    if hasattr(rv, "_parent"):
        rv._parent = parent
    return rv


def make_values_navigable(d):
    """Returns a new dict mapping the keys of the input dict to navigable
    versions of its values."""
    nd = {}
    nd.update({k: make_navigable(v, parent=nd) for k, v in d.items()})
    return nd
