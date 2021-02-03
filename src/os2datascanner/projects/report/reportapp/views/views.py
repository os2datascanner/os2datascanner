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

from datetime import timedelta, datetime
from urllib.parse import urlencode
from django.conf import settings

from django.db.models import Count
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import View, TemplateView, ListView
from django.db.models import Q

from ..models.documentreport_model import DocumentReport
from ..models.roles.defaultrole_model import DefaultRole
from ..models.userprofile_model import UserProfile
from ..models.organization_model import Organization
from ..models.roles.remediator_model import Remediator
from ..models.roles.dpo_model import DataProtectionOfficer
from ..models.roles.leader_model import Leader

from os2datascanner.engine2.rules.cpr import CPRRule
from os2datascanner.engine2.rules.regex import RegexRule
from os2datascanner.engine2.rules.rule import Sensitivity

logger = structlog.get_logger()

RENDERABLE_RULES = (CPRRule.type_label, RegexRule.type_label,)


class LoginRequiredMixin(View):
    """Include to require login."""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """Check for login and dispatch the view."""
        return super().dispatch(*args, **kwargs)


class LoginPageView(View):
    template_name = 'login.html'


class LogoutPageView(TemplateView, View):
    template_name = 'logout.html'


class MainPageView(ListView, LoginRequiredMixin):
    template_name = 'index.html'
    paginate_by = 10  # Determines how many objects pr. page.
    context_object_name = "matches"  # object_list renamed to something more relevant
    model = DocumentReport
    matches = DocumentReport.objects.filter(
        data__matches__matched=True).filter(
        resolution_status__isnull=True)
    scannerjob_filters = None
    roles = None

    def get_queryset(self):
        user = self.request.user
        roles = user.roles.select_subclasses() or [DefaultRole(user=user)]
        # Handles filtering by role + org and sets datasource_last_modified if non existing
        self.matches = filter_inapplicable_matches(user, self.matches, roles)
        # Filters by datasource_last_modified.
        # lt mean less than.
        # gte means greater than or equal to
        # A check whether something is more recent than a month
        # is done by subtracting 30 days from now and then comparing if the saved time is "bigger" than that
        # and vice versa/smaller for older than.
        if self.request.GET.get('30-days') == "true":
            time_threshold = datetime.now() - timedelta(days=30)
            newer_than_30_days = self.matches.filter(
                datasource_last_modified__gt=time_threshold)
            self.matches = newer_than_30_days
        else:
            # Exactly 30 days is deemed to be "older than 30 days"
            # and will therefore be shown.
            time_threshold = datetime.now() - timedelta(days=30)
            older_than_30_days = self.matches.filter(
                datasource_last_modified__lte=time_threshold)
            self.matches = older_than_30_days

        if self.request.GET.get('scannerjob') \
                and self.request.GET.get('scannerjob') != 'all':
            # Filter by scannerjob
            self.matches = self.matches.filter(
                data__scan_tag__scanner__pk=int(
                    self.request.GET.get('scannerjob'))
            )
        if self.request.GET.get('sensitivities') \
                and self.request.GET.get('sensitivities') != 'all':
            # Filter by sensitivities
            self.matches = self.matches.filter(
                sensitivity=int(
                    self.request.GET.get('sensitivities'))
            )

        # matches are always ordered by sensitivity desc. and probability desc.
        return self.matches, self.roles


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["renderable_rules"] = RENDERABLE_RULES
        context["roles"] = [role.__class__.__name__ for role in self.roles]

        if self.scannerjob_filters is None:
            # Create select options
            self.scannerjob_filters = self.matches.order_by(
                'data__scan_tag__scanner__pk').values(
                'data__scan_tag__scanner__pk').annotate(
                total=Count('data__scan_tag__scanner__pk')
            ).values(
                'data__scan_tag__scanner__name',
                'total',
                'data__scan_tag__scanner__pk'
            )

        context['scannerjobs'] = (self.scannerjob_filters,
                                  self.request.GET.get('scannerjob', 'all'))

        context['30_days'] = self.request.GET.get('30-days', 'false')

        sensitivities = self.matches.order_by(
            '-sensitivity').values(
            'sensitivity').annotate(
            total=Count('sensitivity')
        ).values(
            'sensitivity', 'total'
        )

        context['sensitivities'] = (((Sensitivity(s["sensitivity"]),
                                      s["total"]) for s in sensitivities),
                                    self.request.GET.get('sensitivities', 'all'))

        return context


class StatisticsPageView(TemplateView, LoginRequiredMixin):
    template_name = 'statistics.html'
    context_object_name = "matches"  # object_list renamed to something more relevant
    model = DocumentReport
    matches = DocumentReport.objects.filter(
        data__matches__matched=True)
    handled_matches = matches.filter(
        resolution_status__isnull=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        roles = user.roles.select_subclasses() or [DefaultRole(user=user)]
        context["roles"] = [role.__class__.__name__ for role in roles]
        context["renderable_rules"] = RENDERABLE_RULES

        # Counts the distribution of matches by sensitivity
        sensitivities = self.matches.order_by(
            '-sensitivity').values(
            'sensitivity').annotate(
            total=Count('sensitivity')
        ).values(
            'sensitivity', 'total'
        )

        # Counts the distribution of handled matches by sensitivity
        handled_matches = self.handled_matches.order_by(
            '-sensitivity').values(
            'sensitivity').annotate(
            total=Count('sensitivity')
        ).values(
            'sensitivity', 'total',
        )

        # Counts the distribution of data sources by type
        data_sources = self.matches.order_by(
            'data__matches__handle__type').values(
            'data__matches__handle__type').annotate(
            total=Count('data__matches__handle__type')
        ).values(
            'data__matches__handle__type', 'total',
        )

        # Generators had to be done separate from context because of the json_script parser
        sensitivities_gen = (((Sensitivity(s["sensitivity"]),
                                            s["total"]) for s in sensitivities))

        handled_matches_gen = (((Sensitivity(hm["sensitivity"]),
                                            hm["total"]) for hm in handled_matches))

        # Context done as list of tuples
        context['sensitivities'] = [(s[0].presentation,
                                    s[1]) for s in sensitivities_gen]

        context['handled_matches'] = [(hm[0].presentation,
                                      hm[1]) for hm in handled_matches_gen]
        context['data_sources'] = [(ds['data__matches__handle__type'],
                                    ds['total']) for ds in data_sources]

        return context


class ApprovalPageView(TemplateView):
    template_name = 'approval.html'


class StatsPageView(TemplateView):
    template_name = 'stats.html'


class SettingsPageView(TemplateView):
    template_name = 'settings.html'


class AboutPageView(TemplateView):
    template_name = 'about.html'


# Logic separated to function to allow usability in send_notifications.py
def filter_inapplicable_matches(user, matches, roles):
    """ Filters matches by organization
    and role. """

    # Filter by organization
    try:
        user_organization = user.profile.organization
        # Include matches without organization (backwards compatibility)
        matches = matches.filter(Q(organization=None) | Q(organization=user_organization))
    except UserProfile.DoesNotExist:
        # No UserProfile has been set on the request user
        # Default action depends on how many organization objects we have
        # If more than one exist, limit matches to ones without an organization (safety measure)
        if Organization.objects.count() > 1:
            matches = matches.filter(organization=None)

    for role in roles:
        # Filter matches by role.
        matches = role.filter(matches)

    return matches


def oidc_op_logout_url_method(request):
    logout_url = settings.LOGOUT_URL
    return_to_url = settings.LOGOUT_REDIRECT_URL
    return logout_url + '?' + urlencode({'redirect_uri': return_to_url, 'client_id': settings.OIDC_RP_CLIENT_ID})
