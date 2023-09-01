from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from os2datascanner.engine2.model.core.handle import Handle
from os2datascanner.engine2.utilities.datetime import (
        parse_datetime, unparse_datetime)


@dataclass
class Link:
    url: str
    # combine public link_text with setter
    # https://stackoverflow.com/a/61191878
    link_text: Optional[str]
    _link_text: Optional[str] = field(init=False, repr=False)

    @property
    def link_text(self):
        return self._link_text

    @link_text.setter
    def link_text(self, s: Optional[str]):
        # remove newlines and extra whitespace
        if isinstance(s, str):
            s = " ".join([s.strip() for s in s.split()])
        self._link_text = s


class OutputType(Enum):
    """Conversion functions return a typed result, and the type is a member of
    the OutputType enumeration. The values associated with these members are
    simple string identifiers that can be used in serialisation formats."""
    Text = "text"  # str
    LastModified = "last-modified"  # datetime.datetime
    ImageDimensions = "image-dimensions"  # (int, int)
    Links = "links"  # list[Link]
    Manifest = "manifest"  # list[Handle]
    EmailHeaders = "email-headers"  # dict[str, str]

    AlwaysTrue = "fallback"  # True
    NoConversions = "dummy"

    def encode_json_object(self, v):
        """Converts an object (of the appropriate type for this OutputType) to
        a JSON-friendly representation."""
        if v is None:
            return None

        match self:
            case OutputType.Text:
                return str(v)
            case OutputType.LastModified:
                return unparse_datetime(v)
            case OutputType.ImageDimensions:
                return [int(v[0]), int(v[1])]
            case OutputType.Links:
                if isinstance(v, list):
                    return [(link.url, link.link_text) for link in v]
                return (v.url, v.link_text)
            case OutputType.Manifest:
                return [h.to_json_object() for h in v]
            case OutputType.EmailHeaders:
                # v is already suitable for JSON serialisation
                return v

            case OutputType.AlwaysTrue:
                return True
            case _:
                raise TypeError(self.value)

    def decode_json_object(self, v):
        """Constructs an object (of the appropriate type for this OutputType)
        from a JSON representation."""
        if v is None:
            return None

        match self:
            case OutputType.Text:
                return v
            case OutputType.LastModified:
                return parse_datetime(v)
            case OutputType.ImageDimensions:
                return int(v[0]), int(v[1])
            case OutputType.Links:
                return [Link(url, link_text) for url, link_text in v]
            case OutputType.Manifest:
                return [Handle.from_json_object(h) for h in v]
            case OutputType.EmailHeaders:
                # Force all keys to be lower-case
                return {k.lower(): v for k, v in v.items()}

            case OutputType.AlwaysTrue:
                return True
            case _:
                raise TypeError(self.value)


def encode_dict(d):
    """Given a dictionary from OutputType values to objects, returns a new
    dictionary in which each of those objects has been converted to a
    JSON-friendly representation."""
    return {t: OutputType(t).encode_json_object(v) for t, v in d.items()}


def decode_dict(d):
    """Given a dictionary from OutputType values to JSON representations of
    objects, returns a new dictionary in which each of those representations
    has been converted back to an original object."""
    return {t: OutputType(t).decode_json_object(v) for t, v in d.items()}
