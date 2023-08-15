import os
from urllib.parse import urlsplit

from django.apps import apps
from django import template
from django.conf import settings

from os2datascanner.engine2.model.core import Handle
from os2datascanner.engine2.model.smb import SMBHandle
from os2datascanner.engine2.model.smbc import SMBCHandle

from ..models.documentreport import DocumentReport
from ..models.roles.defaultrole import DefaultRole
from ..models.roles.remediator import Remediator
from ..utils import user_is
from ..views.report_views import RENDERABLE_RULES

register = template.Library()


@register.filter
def present(handle):
    """Returns the presentation of the given Handle."""
    if isinstance(handle, Handle):
        return str(handle)
    else:
        return None


@register.filter
def present_url(handle):
    """Returns the renderable presentation URL of the given Handle (or, if it
    doesn't define one, of its first parent that does).

    A "renderable presentation URL" is a presentation URL that isn't None and
    whose scheme is present in the PERMITTED_URL_SCHEMES setting."""

    def _test_handle(handle):
        url = handle.presentation_url
        if url:
            scheme = urlsplit(url)[0]
            if scheme in settings.PERMITTED_URL_SCHEMES:
                return url
        return None
    if isinstance(handle, Handle):
        while not _test_handle(handle) and handle.source.handle:
            handle = handle.source.handle
        return _test_handle(handle)
    else:
        return None


@register.filter
def find_parent(handle, type_label):
    """If the given Handle's type label matches the argument, then returns it;
    otherwise, returns the first parent Handle with that appropriate type label
    (or None if there wasn't one)."""
    if isinstance(handle, Handle):
        while handle and handle.type_label != type_label:
            handle = handle.source.handle
        return handle
    else:
        return None


@register.filter
def find_type_label(handle):
    """Finds the top level handles type_label and then returns it;
    (or None if there wasn't one)."""
    if isinstance(handle, Handle):
        while handle and handle.type_label:
            if handle.source.handle:
                handle = handle.source.handle
            else:
                break
        return handle.type_label
    else:
        return None


@register.filter
def find_svg_icon(type_label):
    svg_dir = "components/svg-icons"
    full_path = os.path.join(
        os.path.join(apps.get_app_config('os2datascanner_report').path,
                     f"templates/{svg_dir}/"), f"icon-{type_label}.svg")
    return os.path.join(
        svg_dir, f"icon-{type_label}.svg") if os.path.exists(full_path) else \
        f"{svg_dir}/icon-default.svg"


@register.simple_tag
def find_scan_type(type_label):
    match type_label:
        case "smbc" | "dropbox" | "googledrive" | "msgraph-file":
            return "File"
        case "msgraph-drive":
            return "MS Teams file"
        case "gmail" | "ews" | "msgraph-mail":
            return "Mail"
        case "web":
            return "Web"
        case _:
            return "Unrecognized file type"


@register.filter
def find_file_folder(handle, force=False):
    """Removes the filename of a match and then returns it (the folder where
    the file is placed"""
    if isinstance(handle, (SMBHandle, SMBCHandle)):
        # the force variable is only for testing, since 'file'-protocol is
        # not allowed by default
        if force:
            file_path = handle.presentation_url
            file_path = file_path[:file_path.rfind('/')]
            return file_path
        if present_url(handle):
            file_path = present_url(handle)
            file_path = file_path[:file_path.rfind('/')]
            return file_path
        else:
            return None


@register.filter
def present_folder(handle):
    """Removes the filename from the path and returns
    the folderpath for copying
    """
    if isinstance(handle, (SMBHandle, SMBCHandle)):
        if present(handle):
            file_path = present(handle)
            file_path = file_path[:file_path.rfind('\\')]
            return file_path
        else:
            return None


@register.filter
def between(lst, interval):
    if interval is None:
        interval = (0, 10)
    return lst[interval[0]:interval[1]]


@register.filter
def get_matchcount(account):
    all_matches = DocumentReport.objects.filter(
        resolution_status__isnull=True,
        number_of_matches__gte=1, organization=account.organization)
    matches = DefaultRole(user=account.user).filter(all_matches)
    if user_is(account.user.roles.all(), Remediator):
        matches = matches | Remediator(user=account.user).filter(all_matches)

    return matches.count()


@register.filter
def is_remediator(user):
    return Remediator.objects.filter(user=user).exists()


@register.filter
def merge_renderable_match_fragments(match_fragments: list):
    """ Provided a list of MatchFragment objects, verifies
    that these contain matches of renderable rules.
    Merges together matches to one result if there are multiple MatchFragments objects."""

    # TODO: Refactor hit.html and this. It is a bit hacky and fragile.
    match_fragments = [frag for frag in match_fragments
                       if frag.rule.type_label in RENDERABLE_RULES
                       and frag.matches]

    if len(match_fragments) >= 2:
        merged_fragment = match_fragments[0]
        merged_fragment.matches.extend(
            match
            for fragment in match_fragments[1:]
            for match in fragment.matches
        )
        return merged_fragment
    else:
        return match_fragments[0]
