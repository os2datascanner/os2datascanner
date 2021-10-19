from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from dateutil import tz
from typing import Optional


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

    AlwaysTrue = "fallback"  # True
    NoConversions = "dummy"

    def encode_json_object(self, v):
        """Converts an object (of the appropriate type for this OutputType) to
        a JSON-friendly representation."""
        if v is None:
            return None
        elif self == OutputType.Text:
            return str(v)
        elif self == OutputType.LastModified:
            return _datetime_to_str(v)
        elif self == OutputType.ImageDimensions:
            return [int(v[0]), int(v[1])]
        elif self == OutputType.Links:
            if isinstance(v, list):
                return [(link.url, link.link_text) for link in v]
            return (v.url, v.link_text)
        elif self == OutputType.AlwaysTrue:
            return True
        else:
            raise TypeError(self.value)

    def decode_json_object(self, v):
        """Constructs an object (of the appropriate type for this OutputType)
        from a JSON representation."""
        if v is None:
            return None
        elif self == OutputType.Text:
            return v
        elif self == OutputType.LastModified:
            return _str_to_datetime(v)
        elif self == OutputType.ImageDimensions:
            return int(v[0]), int(v[1])
        elif self == OutputType.Links:
            return [Link(url, link_text) for url, link_text in v]
        elif self == OutputType.AlwaysTrue:
            return True
        else:
            raise TypeError(self.value)


DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def _datetime_to_str(d):
    if not d.tzinfo or d.tzinfo.utcoffset(d) is None:
        d = d.replace(tzinfo=tz.gettz())
    return d.strftime(DATE_FORMAT)


def _str_to_datetime(s):
    return datetime.strptime(s, DATE_FORMAT)


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
