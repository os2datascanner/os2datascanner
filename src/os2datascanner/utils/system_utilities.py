import re
import json
from datetime import datetime

from os2datascanner.engine2.conversions.types import DATE_FORMAT


def json_utf8_decode(body):
    try:
        body = json.loads(body.decode("utf-8"))
    except UnicodeDecodeError as ue:
        print('Error message: {0}'.format(ue))
        return None
    except json.JSONDecodeError as je:
        # TODO: What should happen if json data is corrupt?
        print('Error message: {0}'.format(je))
        print("* Invalid JSON: {0}".format(body))
        return None

    return body


fixup = re.compile(r"(?P<s>[+-])(?P<h>\d{2}):(?P<m>\d{2})$")
"""Matches ISO 8601 timezone specifiers ("+0000", "-04:00", etc.) at the end of
a timestamp string. Note that this does not match the special specifier "Z",
which is instead given special treatment in parse_isoformat_timestamp."""


def parse_isoformat_timestamp(dt):
    """Parses a string produced by the datetime.isoformat() function back into
    a datetime.datetime, in the process working around a bug in Python versions
    prior to 3.7."""
    # The "%z" str[fp]time format specifier, which is supposed to handle
    # ISO 8601-style time zone specifiers ("Z", "+0200", "-05:30"), doesn't
    # understand colons until Python 3.7. Groan. Work around that by rebuilding
    # the time zone into a supported, colon-less form
    if dt.endswith("Z"):
        dt = dt[:-1] + "+0000"
    match = fixup.search(dt)
    if match:
        replacement = match.group("s") + match.group("h") + match.group("m")
        s, e = match.span()
        dt = dt[:s] + replacement + dt[e:]
    try:
        return datetime.strptime(dt, DATE_FORMAT)
    except ValueError:
        return None
