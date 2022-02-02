import re
import json
import hashlib
import warnings
import structlog

from django.conf import settings
from django.contrib.auth.models import User
from mozilla_django_oidc import auth

from os2datascanner.engine2.pipeline import messages

from .models.aliases.alias_model import Alias
from .models.aliases.emailalias_model import EmailAlias
from .models.aliases.adsidalias_model import ADSIDAlias
from .models.documentreport_model import DocumentReport

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
    has arrived or the old the user_data has been updated.

    The django-saml plugin takes care of the basic user_data such as email, username etc.
    So we do not need to worry about creating or updating the django user."""

    saml_attr = settings.SAML2_AUTH.get('ATTRIBUTES_MAP')
    username = get_user_data(saml_attr.get('username'), user_data)
    email = get_user_data(saml_attr.get('email'), user_data)
    sid = get_user_data(saml_attr.get('sid'), user_data)
    user = User.objects.get(username=username)
    if email:
        sub_alias, is_created = EmailAlias.objects.get_or_create(user=user, address=email)
        create_alias_and_match_relations(sub_alias)
    if sid:
        sub_alias, is_created = ADSIDAlias.objects.get_or_create(user=user, sid=sid)
        create_alias_and_match_relations(sub_alias)


def user_is(roles, role_cls):
    """Checks whether a list of roles contains a certain role type (role_cls)"""
    return any(isinstance(role, role_cls)
               for role in roles)


class OIDCAuthenticationBackend(auth.OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super(OIDCAuthenticationBackend, self).create_user(claims)
        get_claim_user_info(claims, user)
        user.save()
        get_or_create_user_aliases_OIDC(
            user,
            email=claims.get('email', ''),
            sid=claims.get('sid', ''))

        # self.update_groups(user, claims)

        return user

    def update_user(self, user, claims):
        get_claim_user_info(claims, user)
        user.save()
        get_or_create_user_aliases_OIDC(
            user,
            email=claims.get('email', ''),
            sid=claims.get('sid', ''))
        # self.update_groups(user, claims)

        return user


def get_claim_user_info(claims, user):
    user.username = claims.get('preferred_username', '')
    user.first_name = claims.get('given_name', '')
    user.last_name = claims.get('family_name', '')


def get_or_create_user_aliases_OIDC(user, email, sid):  # noqa: D401
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
    batch_size objects.

    This function behaves appropriately when the caller modifies batches in a
    way that shrinks the size of the input QuerySet."""
    # Make sure the QuerySet is ordered -- slicing (i.e., OFFSET/LIMIT in the
    # underlying SQL statement) is otherwise not well-defined
    # (XXX: should we just always impose this ordering in order to make the
    # offset trickery below safer?)
    if not queryset.ordered:
        queryset = queryset.order_by("pk")
    i = 0
    total_count = queryset.count()
    while i < total_count:
        batch = queryset[i: batch_size + i]
        batch_count = batch.count()
        yield batch

        # The operations performed by the caller might have reduced the size of
        # the QuerySet. If that has happened, then reduce the new database
        # offset so that we don't skip over any objects
        new_total = queryset.count()
        count_diff = new_total - total_count
        i += batch_count
        if count_diff < 0:
            i += count_diff
        total_count = new_total


def get_max_sens_prop_value(doc_report_obj, key):
    """Helper method for migration 0017_documentreport_added_sensitivity_and_probability.
    This method returns either a Sensitivity object or probability maximum value.
    The method is located in utils as could become handy else where."""

    if not hasattr(doc_report_obj, "data"):
        raise NotImplementedError()

    if (doc_report_obj.data
            and "matches" in doc_report_obj.data
            and doc_report_obj.data["matches"]):
        return getattr(messages.MatchesMessage.from_json_object(
            doc_report_obj.data["matches"]), key)


def create_alias_and_match_relations(sub_alias):
    """Method for creating match_relations for a given alias
    with all the matching DocumentReports"""
    tm = Alias.match_relation.through

    # Although RFC 5321 says that the local part of an email address
    # -- the bit to the left of the @ --
    # is case sensitive, the real world disagrees..
    if isinstance(sub_alias, EmailAlias):
        reports = DocumentReport.objects.filter(raw_metadata__metadata__contains={
                        str(sub_alias.key): str(sub_alias).lower()})
    else:
        reports = DocumentReport.objects.filter(raw_metadata__metadata__contains={
                        str(sub_alias.key): str(sub_alias)})
    tm.objects.bulk_create([tm(documentreport_id=r.pk, alias_id=sub_alias.pk)
                            for r in reports], ignore_conflicts=True)


def get_msg(query):
    """ Utility function used in get_presentation,
        which is used in migration 0033_add_sort_key_and_name_charfield
        and in management command refresh_sort_key.
        """
    if not hasattr(query, "data"):
        raise NotImplementedError()

    # only one of these are not None
    matches = query.data.get("matches")
    metadata = query.data.get("metadata")
    problem = query.data.get("problem")

    if matches:
        return messages.MatchesMessage.from_json_object(matches)
    elif problem:
        problem = messages.ProblemMessage.from_json_object(problem)
        # problemMessage have optional handle and source fields. Try the latter if
        # the first is None.
        if not problem.handle:
            problem = problem.source if problem.source else problem
        return problem
    elif metadata:
        return messages.MetadataMessage.from_json_object(metadata)
    else:
        return None


def get_presentation(query):
    """ Utility function used in used in migration 0033_add_sort_key_and_name_charfield
        and in management command refresh_sort_key.
        Returns handle of a message"""

    type_msg = get_msg(query)
    if not type_msg:
        return ""

    return type_msg.handle if type_msg.handle else ""


def prepare_json_object(o):
    """Processes an object suitable for JSON serialisation to make it suitable
    for storing in the OS2datascanner report module's database. (At the moment
    this just means removing all null bytes and PEP 383 surrogate pairs from
    string values, as PostgreSQL can't deal with them in any string or JSON
    data type.)"""
    if isinstance(o, dict):
        return {prepare_json_object(k): prepare_json_object(v)
                for k, v in o.items()}
    elif isinstance(o, (list, tuple)):
        return [prepare_json_object(i) for i in o]
    elif isinstance(o, str):
        if "\0" in o:
            warnings.warn(
                    "stripping null byte for PostgreSQL compatibility",
                    UnicodeWarning)
            o = o.replace("\0", "")
        if re.search(r'[\uD800-\uDFFF]', o):
            warnings.warn(
                    "stripping illegal surrogates for PostgreSQL compatibility",
                    UnicodeWarning)
            o = re.sub(r'[\uD800-\uDFFF]', '\ufffd', o)
        return o
    else:
        return o
