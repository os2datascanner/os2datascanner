import datetime
from dateutil.parser import parse
from dateutil.tz import gettz


def parse_datetime(val: str, local: bool = False) -> datetime.datetime:
    """Parses an input string as though with dateutil.parser.parse, and returns
    a datetime.datetime guaranteed to be timezone-aware.

    If the local flag is not specified or is False, then UTC will be used as
    the default fallback timezone; if it's True, then the system's local
    timezone will be used instead."""
    rv = parse(val)
    if not rv.tzinfo:
        rv = rv.replace(tzinfo=datetime.timezone.utc if not local else gettz())
    return rv


DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def unparse_datetime(d: datetime.datetime) -> str:
    if not d.tzinfo or d.tzinfo.utcoffset(d) is None:
        d = d.replace(tzinfo=gettz())
    return d.strftime(DATE_FORMAT)
