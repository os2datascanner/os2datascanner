import re
from datetime import datetime
import json
import hashlib
import structlog

from django.conf import settings
from django.contrib.auth.models import User

from os2datascanner.engine2.conversions.types import DATE_FORMAT
from .models.aliases.emailalias_model import EmailAlias
from .models.aliases.adsidalias_model import ADSIDAlias


logger = structlog.get_logger()
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


def hash_handle(handle):
    """
    Creates a SHA-512 hash value from the handle string
    and returns the hex value.
    :param handle: handle as json object
    :return: SHA-512 hex value
    """
    return hashlib.sha512(json.dumps(handle).encode()).hexdigest()

def get_or_create_user_aliases(user_data):  # noqa: D401
    """Hook called after user is created, during SAML login, in DB and before login.
    This method creates or updates the users aliases depending on if new user_data
    has arrived or the old the user_data has been updated.

    The django-saml plugin takes care of the basic user_data such as email, username etc.
    So we do not need to worry about creating or updating the django user."""

    saml_attr = settings.SAML2_AUTH.get('ATTRIBUTES_MAP')
    username = get_user_data(saml_attr.get('username'), user_data)
    email = get_user_data(saml_attr.get('email'), user_data)
    sid = get_user_data(saml_attr.get('sid'), user_data)
    user = User.objects.get(username=username)
    if email:
        EmailAlias.objects.get_or_create(user= user, address=email)
    if sid:
        ADSIDAlias.objects.get_or_create(user=user, sid=sid)

def get_user_data(key, user_data):
    """Helper method for retrieving data for a given key."""
    data = None
    try:
        data = user_data.get(key)[0]
    except TypeError:
        logger.warning('User data does not contain '
                       'any value for key {}'.format(key))
    return data


