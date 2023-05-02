import hashlib


def get_state(obj):
    """Gets the uniqueness identifiers for the given object, allowing
    comparisons in eg. queries. Be warned! If you add another field to the
    `eq_properties` of an object, either that field must be None by default,
    or a migration may have to be made to update certain equality fields on
    existing objects (take DocumentReport.path as an example)."""
    if hasattr(obj, 'eq_properties'):
        return {k: getattr(obj, k) for k in getattr(obj, 'eq_properties')}
    elif hasattr(obj, '__getstate__'):
        return obj.__getstate__()
    else:
        return obj.__dict__


class TypePropertyEquality:
    """Classes inheriting from the TypePropertyEquality mixin compare equal if
    their type objects and properties compare equal.

    The relevant properties for this purpose are, in order of preference:
    - those enumerated by the 'eq_properties' field;
    - the keys of the dictionary returned by its __getstate__ function; or
    - the keys of its __dict__ field."""

    def __eq__(self, other):
        return (isinstance(self, type(other)) and
                get_state(self) == get_state(other))

    def __hash__(self):
        try:
            h = 42 + hash(type(self))
            for k, v in get_state(self).items():
                h += hash(k) + (hash(v) * 3)
            return h
        except Exception as ex:
            raise TypeError(
                    f"{type(self)!s}.__hash__()") from ex

    def crunch(self, *, hash=None) -> str:
        """Returns a (not very human readable) string summary of all of the
        relevant properties of this TypePropertyEquality object. This value is
        useful as a primary key for this object in database systems.

        (Note that properties with a value of None will not appear in the
        summary. Consider using this as a default value for relevant properties
        to avoid having to recompute primary keys.)"""
        fragments = []

        for prop, raw_value in get_state(self).items():
            if raw_value is None:
                continue

            fragment = f"{prop}="
            if isinstance(raw_value, TypePropertyEquality):
                fragment += f"({raw_value.crunch()})"
            else:
                fragment += str(raw_value)

            fragments.append(fragment)

        # The format of this string is something like:
        # Handle(_source=(Source(_unc=//path/to/somewhere));_relpath=some_file.txt)
        rv = type(self).__name__ + "(" + ";".join(fragments) + ")"

        if hash is not None:
            if hash in (True, "sha512"):
                return hashlib.sha512(rv.encode("unicode_escape")).hexdigest()
            else:
                raise ValueError(f"Unrecognised crunch hash '{hash}'")
        else:
            return rv
