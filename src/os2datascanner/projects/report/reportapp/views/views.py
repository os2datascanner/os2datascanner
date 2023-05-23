#!/usr/bin/env python
# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2datascanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (https://os2.eu/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( https://os2.eu/ )
import structlog

from urllib.parse import urlencode
from django.conf import settings

from django.core.paginator import Paginator, EmptyPage
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View, TemplateView
from django.http import Http404

from os2datascanner.engine2.rules.cpr import CPRRule
from os2datascanner.engine2.rules.regex import RegexRule
from os2datascanner.engine2.rules.name import NameRule
from os2datascanner.engine2.rules.address import AddressRule
from os2datascanner.engine2.rules.links_follow import LinksFollowRule
from os2datascanner.engine2.rules.wordlists import OrderedWordlistRule

from ..utils import user_is, user_is_superadmin
from ..models.roles.defaultrole import DefaultRole
from ..models.roles.remediator import Remediator
from ...organizations.models.account import Account


logger = structlog.get_logger()

RENDERABLE_RULES = (
    CPRRule.type_label, RegexRule.type_label, LinksFollowRule.type_label,
    OrderedWordlistRule.type_label, NameRule.type_label, AddressRule.type_label
)


class LogoutPageView(TemplateView, View):
    template_name = 'logout.html'


class EmptyPagePaginator(Paginator):
    def validate_number(self, number):
        try:
            return super(EmptyPagePaginator, self).validate_number(number)
        except EmptyPage:
            if number > 1:
                return self.num_pages
            else:
                raise Http404(_('The page does not exist'))


class ApprovalPageView(TemplateView):
    template_name = 'approval.html'


class StatsPageView(TemplateView):
    template_name = 'stats.html'


class SettingsPageView(TemplateView):
    template_name = 'settings.html'


class AboutPageView(TemplateView):
    template_name = 'about.html'


# Logic separated to function to allow usability in send_notifications.py
def filter_inapplicable_matches(user, matches, roles, account=None):
    """ Filters matches by organization
    and role. """

    # Filter by organization
    try:
        user_organization = user.account.organization
        if user_organization:
            matches = matches.filter(organization=user_organization)
    except Account.DoesNotExist:
        # No Account has been set on the request user
        # Check if we have received an account as arg (from send_notifications.py) and use
        # its organization to locate matches.
        if account:
            matches = matches.filter(organization=account.organization)

    if user_is_superadmin(user):
        hidden_matches = matches.filter(only_notify_superadmin=True)
        user_matches = DefaultRole(user=user).filter(matches)
        matches_all = hidden_matches | user_matches
    else:
        matches_all = DefaultRole(user=user).filter(matches)
        matches_all = matches_all.filter(only_notify_superadmin=False)

    if user_is(roles, Remediator):
        unassigned_matches = Remediator(user=user).filter(matches)
        matches = unassigned_matches | matches_all
    else:
        matches = matches_all

    return matches


def oidc_op_logout_url_method(request):
    logout_url = settings.LOGOUT_URL
    return_to_url = settings.LOGOUT_REDIRECT_URL
    return logout_url + '?' + urlencode({'redirect_uri': return_to_url,
                                         'client_id': settings.OIDC_RP_CLIENT_ID})
