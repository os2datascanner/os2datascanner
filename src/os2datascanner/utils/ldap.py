from typing import (
        Tuple, Union, Callable, Iterator, Optional, Sequence, NamedTuple,
        MutableSequence)
import logging
from itertools import zip_longest


logger = logging.getLogger(__name__)


_scs = """ "#+,;<=>\\"""
_hex = "0123456789abcdef"


def ldap_split(s: str, codec: str = "utf-8") -> Sequence[str]:
    """Splits a string representation of a LDAP Distinguished Name according to
    the rules laid out in RFC 4514.

    DNs represent extended characters as escaped bytes in an unspecified
    character set. Using UTF-8, for example, U+00C5 "Å" would become "\C3\85".
    (LDAPv3 requires that UTF-8 be used, and Active Directory obeys this when
    running in LDAPv3 mode.)"""
    tokens = []
    token = bytes()
    iterator = iter(s)
    while True:
        try:
            here = next(iterator)
        except StopIteration:
            nt = token.decode(codec)
            # A completely empty string *is* a valid (if empty) RDN, so this
            # case is only an error if we know we have other tokens
            if "=" not in nt and tokens:
                raise ValueError(f"Invalid RDN: {nt}")
            tokens.append(nt)
            break
        if here == ",":
            nt = token.decode(codec)
            if "=" not in nt:
                raise ValueError(f"Invalid RDN: {nt}")
            tokens.append(nt)
            token = bytes()
        elif here == "\\":
            try:
                n1 = next(iterator).lower()
                if n1 in _scs:
                    token += n1.encode(codec)
                elif n1 in _hex:
                    n2 = next(iterator).lower()
                    if n2 in _hex:
                        raw = (_hex.index(n1) * 16) + _hex.index(n2)
                        # 'big' here is the byte order, but that's irrelevant
                        # if we're only producing one byte!
                        token += raw.to_bytes(1, 'big')
                    else:
                        raise ValueError(f"Invalid escape sequence: {n1}{n2}")
                else:
                    raise ValueError(f"Invalid escape sequence: {n1}")
            except StopIteration:
                raise ValueError("Incomplete escape sequence")
        else:
            token += here.encode(codec)

    return tokens


def ldap_escape(s: str, codec: str = "utf-8"):
    """Escapes a RDN fragment according to the rules laid out in RFC 4514.

    By default, Unicode characters are converted to their representation in the
    given codec and escaped as hex digits. To avoid this conversion, specify a
    codec of None."""
    v = ""
    final = len(s) - 1
    for position, c in enumerate(s):
        if c in _scs:
            # Spaces only need to be escaped at the beginning and at the end of
            # each token; comments only need to be escaped at the beginning
            if ((c == "#" and position != 0)
                    or (c == " " and position not in (0, final))):
                v += c
            else:
                v += f"\\{c}"
        elif codec is not None and ord(c) > 127:
            v += "".join(f"\\{b:02x}" for b in c.encode(codec))
        else:
            v += c
    return v


class RDN(NamedTuple):
    """A relative distinguished name, a key-value pair used to identify LDAP
    fragments.

    RDNs are usually used in a sequence to represent a complete distinguished
    name. (The static utility methods associated with this class flip the
    ordering of these sequences so that the largest RDN comes first.)"""
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
    def dn_to_sequence(dn: str, codec: str = "utf-8") -> Sequence['RDN']:
        """Converts a string representation of a distinguished name into a
        sequence of relative distinguished names."""
        return tuple(
                RDN(k, v)
                for k, v in (
                        s.split("=", 1)
                        for s in reversed(ldap_split(dn))
                        if s))

    @staticmethod
    def sequence_to_dn(rdns: Sequence['RDN'], codec: str = "utf-8") -> str:
        """Converts a sequence of relative distinguished names into a string
        representation."""
        return ",".join(
                f"{ldap_escape(k, codec)}={ldap_escape(v, codec)}"
                for k, v in reversed(rdns))


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
        dn = RDN.dn_to_sequence(name)
        for group_name in groups:
            gdn = RDN.dn_to_sequence(group_name)
            if gdn:  # Only yield names for valid groups
                yield RDN.sequence_to_dn(gdn + (dn[-1],))


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
        return RDN.sequence_to_dn(self.label)

    def __repr__(self) -> str:
        return str(self) + f" <{len(self.children)}>"

    def walk(self, *, _parents: Sequence[RDN] = ()
            ) -> Iterator[Tuple[Sequence[RDN], 'LDAPNode']]:
        """Enumerates all LDAPNodes in this hierarchy in depth-first order,
        along with their full distinguished names."""
        yield (_parents + self.label, self)
        for k in self.children:
            yield from k.walk(_parents=_parents + self.label)

    def diff(self, other: 'LDAPNode', *, only_leaves: bool = False
            ) -> Iterator[
                Tuple[Sequence[RDN], Optional['LDAPNode'], Optional['LDAPNode']]]:
        """Computes the difference between this LDAPNode hierarchy and another
        one. (By default, the diff includes all nodes, but setting @only_leaves
        to True will skip any nodes that have children.)"""
        our_nodes = {k: v for k, v in self.walk()
                if not v.children or not only_leaves}
        their_nodes = {k: v for k, v in other.walk()
                if not v.children or not only_leaves}
        ours = our_nodes.keys()
        theirs = their_nodes.keys()

        yield from ((k, our_nodes[k], None) for k in ours - theirs)
        yield from ((k, our_nodes[k], their_nodes[k])
                for k in ours & theirs if our_nodes[k] != their_nodes[k])
        yield from ((k, None, their_nodes[k]) for k in theirs - ours)

    def print(self, *, _levels: int = 0):
        """Prints a summary of this LDAP node and its descendants to the
        console."""
        print("  " * _levels, RDN.sequence_to_dn(self.label))
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

        for item in iterator:
            try:
                names = tuple(name_selector(item))
            except Exception:
                logger.exception(f"unexpected error while parsing {item}")
                raise

            if not names:
                logger.warning(
                        f"{item} has no valid names and so will not appear "
                        "in the LDAP hierarchy")
                continue
            else:
                for name in names:
                    dn = RDN.dn_to_sequence(name)
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
