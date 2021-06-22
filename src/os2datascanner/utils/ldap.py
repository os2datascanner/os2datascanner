from typing import (
        Tuple, Union, Callable, Iterator, Optional, Sequence, NamedTuple,
        MutableSequence)
from itertools import zip_longest


class RDN(NamedTuple):
    """A relative distinguished name, a key-value pair used to identify LDAP
    fragments.

    RDNs are almost always used as sequences."""
    key: str
    value: str

    def __str__(self):
        return f"{self.key}={self.value}"

    @staticmethod
    def drop_start(
            longer: Sequence['RDN'],
            shorter: Sequence['RDN']) -> Sequence['RDN']:
        local_name_part = tuple(zip_longest(longer, shorter))
        while local_name_part:
            lp, sp = local_name_part[0]
            if lp != sp:
                break
            else:
                local_name_part = local_name_part[1:]
        return tuple(lp for (lp, _) in local_name_part)

    @staticmethod
    def make_sequence(*strings: str) -> Sequence['RDN']:
        return tuple(RDN(k, v)
                for k, v in (s.split("=", 1) for s in reversed(strings) if s))

    @staticmethod
    def make_string(rdns: Sequence['RDN']) -> str:
        return ",".join(str(l) for l in reversed(rdns))


def trivial_dn_selector(d):
    """Name selector function for use with LDAPNode.from_iterator.

    Selects a single name from a dictionary representing an LDAP user: its
    distinguished name."""
    name = d.get("distinguishedName")
    if name:
        yield name


def group_dn_selector(d):
    """Name selector function for use with LDAPNode.from_iterator.

    Selects zero or more names from a dictionary representing an LDAP user,
    one for each group it's a member of. Group membership is decided on the
    basis of the "memberOf" attribute, which should contain a list of
    distinguished names."""
    name = d.get("distinguishedName")
    groups = d.get("memberOf")
    if name and groups:
        dn = RDN.make_sequence(*name.strip().split(","))
        for group_name in groups:
            gdn = RDN.make_sequence(*group_name.strip().split(","))
            if gdn:  # Only yield names for valid groups
                yield RDN.make_string(gdn + (dn[-1],))


class LDAPNode(NamedTuple):
    """A node in a X.500/LDAP-style directory. (This is not even slightly
    supposed to be a complete implementation of RFC 4512, but it's enough of
    one for OS2datascanner's purposes.)

    Nodes consist of three things: a label, which is a (possibly empty)
    tuple of relative distinguished names; a list of child nodes; and a
    dictionary of arbitrary properties."""
    label: Sequence[RDN]
    children: MutableSequence['LDAPNode']
    properties: dict

    @staticmethod
    def make(label, *children: 'LDAPNode', **properties) -> 'LDAPNode':
        """The recommended constructor for LDAPNode objects."""
        return LDAPNode(tuple(label), list(children), properties)

    def collapse(self,
            collapse_ok: Callable[['LDAPNode'], bool] =
                    lambda n: True) -> 'LDAPNode':
        """Returns a new simplified LDAP hierarchy: multiple nodes at the top
        with a single child (and for which the collapse_ok function returns
        True) will be reduced to a single node with a multi-part label.."""
        if len(self.children) == 1 and collapse_ok(self):
            child = self.children[0]
            new_properties = self.properties
            new_properties.update(child.properties)
            return LDAPNode.make(
                    self.label + child.label,
                    *child.children, **new_properties).collapse(collapse_ok)
        else:
            return self

    def __str__(self) -> str:
        return RDN.make_string(self.label)

    def __repr__(self) -> str:
        return str(self) + f" <{len(self.children)}>"

    def walk(self, *, _parents: Sequence[RDN] = ()) -> Iterator[
            Tuple[Sequence[RDN], 'LDAPNode']]:
        """Enumerates all LDAPNodes in this hierarchy in depth-first order,
        along with their full distinguished names."""
        yield (_parents + self.label, self)
        for k in self.children:
            yield from k.walk(_parents=_parents + self.label)

    def diff(self, other: 'LDAPNode') -> Iterator[
            Tuple[Sequence[RDN], Tuple['LDAPNode', 'LDAPNode']]]:
        """Computes the difference between this LDAPNode hierarchy and another
        one."""
        our_leaves = {k: v for k, v in self.walk() if not v.children}
        their_leaves = {k: v for k, v in other.walk() if not v.children}
        ours = our_leaves.keys()
        theirs = their_leaves.keys()

        yield from ((k, our_leaves[k], None) for k in ours - theirs)
        yield from ((k, our_leaves[k], their_leaves[k])
                for k in ours & theirs if our_leaves[k] != their_leaves[k])
        yield from ((k, None, their_leaves[k]) for k in theirs - ours)

    def print(self, *, _levels: int = 0):
        """Prints a summary of this LDAP node and its descendants to the
        console."""
        print("  " * _levels, RDN.make_string(self.label))
        for k, v in self.properties.items():
            print("  " * (_levels + 1), f"- {k}: {v}")
        for k in self.children:
            k.print(_levels=_levels + 1)

    @classmethod
    def from_iterator(
            cls,
            iterator: Iterator[dict],
            name_selector: Callable[[dict], Iterator[str]]=
                    trivial_dn_selector):
        """Builds an LDAPNode hierarchy from an iterator of dictionaries
        representing user objects and returns its root. The hierarchy will be
        constructed based on the users' distinguished names. For example, the
        input

        [
            {"distinguishedName": "CN=Enki,L=Eridu,L=Sumer"},
            {"distinguishedName": "CN=Ninhursag,L=Eridu,L=Sumer"},
            {"distinguishedName": "CN=Gilgamesh,L=Uruk,L=Sumer"},
        ]

        would produce the hierarchy

                              (root)
                                |
                             L=Sumer
                            /       \
                     L=Eridu         L=Uruk
                    /       \              \
        CN=Ninhursag         CN=Enki        CN=Gilgamesh

        The name_selector function yields zero or more distinguished names for
        a given dictionary; an equal (but not necessarily identical!) LDAP node
        will appear at each named position in the hierarchy. (A dictionary for
        which zero names are yielded will not appear at all.)

        Each input dictionary is copied verbatim as the properties of the
        resulting LDAP node."""
        root = LDAPNode.make(())

        # It'd be nice if Python's for loops just *supported* guard syntax...
        for item, names in (
                (entry, name_selector(entry)) for entry in iterator):
            for name in names:
                dn = RDN.make_sequence(*name.strip().split(","))

                node = root
                for idx in range(len(dn)):
                    label = (dn[idx],)
                    child = None
                    for ch in node.children:
                        if ch.label == label:
                            child = ch
                            break
                    else:
                        child = LDAPNode.make(label)
                        node.children.append(child)
                    node = child

                node.properties.clear()
                node.properties.update(item)

        return root
