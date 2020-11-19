import json
import hashlib
import unicodedata
import structlog

from django.conf import settings
from django.contrib.auth.models import User
from mozilla_django_oidc import auth

from os2datascanner.engine2.pipeline import messages

from .models.aliases.emailalias_model import EmailAlias
from .models.aliases.adsidalias_model import ADSIDAlias

logger = structlog.get_logger()


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
    has arrived or the old the user_data has been updated."""


class OIDCAuthenticationBackend(auth.OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super(OIDCAuthenticationBackend, self).create_user(claims)
        get_claim_user_info(claims, user)
        user.save()
        get_or_create_user_aliases(user, email=claims.get('email', ''), sid=claims.get('sid', ''))

        # self.update_groups(user, claims)

        return user

    def update_user(self, user, claims):
        get_claim_user_info(claims, user)
        user.save()
        get_or_create_user_aliases(user, email=claims.get('email', ''), sid=claims.get('sid', ''))
        # self.update_groups(user, claims)

        return user


def get_claim_user_info(claims, user):
    user.username = claims.get('preferred_username', '')
    user.first_name = claims.get('given_name', '')
    user.last_name = claims.get('family_name', '')


def get_or_create_user_aliases(user, email, sid):  # noqa: D401
    """ This method creates or updates the users aliases  """
    if email:
        EmailAlias.objects.get_or_create(user=user, address=email)
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


def iterate_queryset_in_batches(batch_size, queryset):
    """Yields everything in the given QuerySet in batches of at most
    batch_size objects."""
    # Make sure the QuerySet is ordered -- slicing (i.e., OFFSET/LIMIT in the
    # underlying SQL statement) is otherwise not well-defined
    if not queryset.ordered:
        queryset = queryset.order_by("pk")
    i = 0
    count = queryset.count()
    while i < count:
        print('i: {}'.format(str(i)))
        batch = queryset[i: batch_size + i]
        yield batch
        i += batch_size


def get_max_sens_prop_value(doc_report_obj, key):
    """Helper method for migration 0014_documentreport_added_sensitivity_and_probability.
    This method returns either a Sensitivity object or probability maximum value.
    The method is located in utils as could become handy else where."""
    if (doc_report_obj.data
            and "matches" in doc_report_obj.data
            and doc_report_obj.data["matches"]):
        return getattr(messages.MatchesMessage.from_json_object(
            doc_report_obj.data["matches"]), key)
