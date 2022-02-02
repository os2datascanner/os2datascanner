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

from datetime import timedelta
from calendar import month_abbr
from collections import deque
from urllib.parse import urlencode
from django.conf import settings

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponseForbidden, Http404
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.views.generic import View, TemplateView, ListView

from os2datascanner.utils.system_utilities import time_now
from os2datascanner.engine2.rules.cpr import CPRRule
from os2datascanner.engine2.rules.regex import RegexRule
from os2datascanner.engine2.rules.links_follow import LinksFollowRule
from os2datascanner.engine2.rules.rule import Sensitivity
from os2datascanner.engine2.rules.wordlists import OrderedWordlistRule
from os2datascanner.projects.report.reportapp.models.roles.role_model import Role

from ..utils import user_is
from ..models.documentreport_model import DocumentReport
from ..models.roles.defaultrole_model import DefaultRole
from ..models.userprofile_model import UserProfile
from ..models.organization_model import Organization
from ..models.roles.remediator_model import Remediator

# For permissions
from ..models.roles.dpo_model import DataProtectionOfficer
from ..models.roles.leader_model import Leader

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = structlog.get_logger()

RENDERABLE_RULES = (
    CPRRule.type_label, RegexRule.type_label, LinksFollowRule.type_label,
    OrderedWordlistRule.type_label,
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


class MainPageView(LoginRequiredMixin, ListView):
    template_name = 'index.html'
    paginator_class = EmptyPagePaginator
    paginate_by = 10  # Determines how many objects pr. page.
    context_object_name = "document_reports"  # object_list renamed to something more relevant
    model = DocumentReport
    document_reports = DocumentReport.objects.filter(
        raw_matches__matched=True).filter(
        resolution_status__isnull=True).order_by("sort_key")
    scannerjob_filters = None
    paginate_by_options = [10, 20, 50, 100, 250]

    def get_queryset(self):
        user = self.request.user
        roles = Role.get_user_roles_or_default(user)
        # Handles filtering by role + org and sets datasource_last_modified if non existing
        self.document_reports = filter_inapplicable_matches(user, self.document_reports, roles)

        # Filters by datasource_last_modified.
        # lte mean less than or equal to.
        # A check whether something is more recent than a month
        # is done by subtracting 30 days from now and then comparing if
        # the saved time is "bigger" than that
        # and vice versa/smaller for older than.
        # By default true and we show all document_reports. If false we only show
        # document_reports older than 30 days
        if self.request.GET.get('30-days') == 'false':
            older_than_30 = time_now() - timedelta(days=30)
            self.document_reports = self.document_reports.filter(
                datasource_last_modified__lte=older_than_30)

        if (scannerjob := self.request.GET.get('scannerjob')) and scannerjob != 'all':
            self.document_reports = self.document_reports.filter(
                scanner_job_pk=int(scannerjob))

        if (sensitivity := self.request.GET.get('sensitivities')) and sensitivity != 'all':
            self.document_reports = self.document_reports.filter(sensitivity=int(sensitivity))

        self.order_queryset_by_property()

        return self.document_reports

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["renderable_rules"] = RENDERABLE_RULES

        if self.scannerjob_filters is None:
            # Create select options
            self.scannerjob_filters = self.document_reports.order_by(
                'scanner_job_pk').values(
                'scanner_job_pk').annotate(
                total=Count('scanner_job_pk')
            ).values(
                'scanner_job_name',
                'total',
                'scanner_job_pk'
            )

        context['scannerjobs'] = (self.scannerjob_filters,
                                  self.request.GET.get('scannerjob', 'all'))

        context['30_days'] = self.request.GET.get('30-days', 'true')

        sensitivities = self.document_reports.order_by(
            '-sensitivity').values(
            'sensitivity').annotate(
            total=Count('sensitivity')
        ).values(
            'sensitivity', 'total'
        )

        context['sensitivities'] = (((Sensitivity(s["sensitivity"]),
                                      s["total"]) for s in sensitivities),
                                    self.request.GET.get('sensitivities', 'all'))

        context['paginate_by'] = int(self.request.GET.get('paginate_by', self.paginate_by))
        context['paginate_by_options'] = self.paginate_by_options

        context['order_by'] = self.request.GET.get('order_by', 'sort_key')
        context['order'] = self.request.GET.get('order', 'ascending')

        return context

    def get_paginate_by(self, queryset):
        # Overrides get_paginate_by to allow changing it in the template
        # as url param paginate_by=xx
        return self.request.GET.get('paginate_by', self.paginate_by)

    # Function for sending message to socket
    def send_socket_message():
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'get_updates',
            {
                'type': 'websocket_receive',
                'message': 'new matches'
            }
        )

    def order_queryset_by_property(self):
        """Checks if a sort key is allowed and orders the querset"""
        allowed_sorting_properties = ['sort_key']
        if (sort_key := self.request.GET.get('order_by')) and (
                order := self.request.GET.get('order')):

            if sort_key not in allowed_sorting_properties:
                return

            if order != 'ascending':
                sort_key = '-'+sort_key
            self.document_reports = self.document_reports.order_by(sort_key)


class StatisticsPageView(LoginRequiredMixin, TemplateView):
    template_name = 'statistics.html'
    context_object_name = "matches"  # object_list renamed to something more relevant
    model = DocumentReport
    users = UserProfile.objects.all()
    matches = DocumentReport.objects.filter(
        raw_matches__matched=True)
    handled_matches = matches.filter(
        resolution_status__isnull=False)
    unhandled_matches = matches.filter(
        resolution_status__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()

        # Contexts are done as lists of tuples
        context['sensitivities'], context['total_matches'] = \
            self.count_all_matches_grouped_by_sensitivity()

        context['handled_matches'], context['total_handled_matches'] = \
            self.count_handled_matches_grouped_by_sensitivity()

        context['source_types'] = self.count_by_source_types()

        context['new_matches_by_month'] = self.count_new_matches_by_month(today)

        context['unhandled_matches_by_month'] = self.count_unhandled_matches_by_month(today)

        return context

    def count_handled_matches_grouped_by_sensitivity(self):
        """Counts the distribution of handled matches grouped by sensitivity"""
        handled_matches = self.handled_matches.order_by(
            '-sensitivity').values(
            'sensitivity').annotate(
            total=Count('sensitivity')
        ).values(
            'sensitivity', 'total',
        )

        return self.create_sensitivity_list(handled_matches)

    def count_all_matches_grouped_by_sensitivity(self):
        """Counts the distribution of matches grouped by sensitivity"""
        sensitivities = self.matches.order_by(
            '-sensitivity').values(
            'sensitivity').annotate(
            total=Count('sensitivity')
        ).values(
            'sensitivity', 'total'
        )

        return self.create_sensitivity_list(sensitivities)

    def create_sensitivity_list(self, matches):
        """Helper method which groups the totals by sensitivities
        and also takes the sum of the totals"""
        # For handling having no values - List defaults to 0
        sensitivity_list = [
            [Sensitivity.CRITICAL.presentation, 0],
            [Sensitivity.PROBLEM.presentation, 0],
            [Sensitivity.WARNING.presentation, 0],
            [Sensitivity.NOTICE.presentation, 0],
        ]
        for match in matches:
            if (match['sensitivity']) == Sensitivity.CRITICAL.value:
                sensitivity_list[0][1] = match['total']
            elif (match['sensitivity']) == Sensitivity.PROBLEM.value:
                sensitivity_list[1][1] = match['total']
            elif (match['sensitivity']) == Sensitivity.WARNING.value:
                sensitivity_list[2][1] = match['total']
            elif (match['sensitivity']) == Sensitivity.NOTICE.value:
                sensitivity_list[3][1] = match['total']

        # Sum of the totals
        total = 0
        for match in sensitivity_list:
            total += match[1]

        return sensitivity_list, total

    def count_by_source_types(self):
        """Counts all matches grouped by source types"""
        matches_counted_by_sources = self.matches.order_by(
            'source_type').values(
            'source_type').annotate(
            total=Count('source_type')
        ).values(
            'source_type', 'total'
        )

        source_count_gen = ((m['source_type'], m['total'])
                            for m in matches_counted_by_sources)

        formatted_counts = [
            [_('Other'), 0],
            [_('Webscan'), 0],
            [_('Filescan'), 0],
            [_('Mailscan'), 0],
        ]

        # Places source_types from generator to formatted_counts
        for s in source_count_gen:
            if s[0] == 'web':
                formatted_counts[1][1] = s[1]
            elif s[0] == 'smbc':
                formatted_counts[2][1] = s[1]
            elif s[0] == 'ews':
                formatted_counts[3][1] = s[1]
            else:
                formatted_counts[0][1] += s[1]

        return formatted_counts

    def get_oldest_matches(self):
        # TODO: Needs to be rewritten if a better 'time' is added(#41326)
        # Gets days since oldest unhandled match for each user
        oldest_matches = []
        now = time_now

        for org_user in self.users:
            Role.get_user_roles_or_default(org_user)
            earliest_date = now
            for match in self.unhandled_matches:
                if match.scan_time < earliest_date:
                    earliest_date = match.scan_time
                days_ago = now - earliest_date
            tup = (org_user.first_name, days_ago.days)
            oldest_matches.append(tup)

        return oldest_matches

    def count_unhandled_matches(self):
        # Counts the amount of unhandled matches
        # TODO: Optimize queries by reading from relational db
        unhandled_matches = self.unhandled_matches.order_by(
            'raw_metadata__metadata').values(
            'raw_metadata__metadata').annotate(
            total=Count('raw_metadata__metadata')
        ).values(
            'raw_metadata__metadata', 'total',
        )

        # TODO: Optimize queries by reading from relational db
        employee_unhandled_list = []
        for um in unhandled_matches:
            dict_values = list(um['raw_metadata__metadata'].values())
            first_value = dict_values[0]
            employee_unhandled_list.append((first_value, um['total']))

        return employee_unhandled_list

    def count_unhandled_matches_by_month(self, current_date):
        """Counts new matches and resolved matches by month for the last year,
        rotates the current month to the end of the list, inserts and subtracts using the counts
        and then makes a running total"""
        a_year_ago = current_date - timedelta(days=365)

        new_matches_by_month = self.matches.filter(
            created_timestamp__range=(a_year_ago, current_date)).annotate(
            month=TruncMonth('created_timestamp')).values(
            'month').annotate(
            total=Count('raw_matches')
        ).order_by('month')

        resolved_matches_by_month = self.handled_matches.filter(
            created_timestamp__range=(a_year_ago, current_date)).annotate(
            month=TruncMonth('resolution_time')).values(
            'month').annotate(
            total=Count('raw_matches')
        ).order_by('month')

        # Generators with months as integers and the counts
        new_matches_by_month_gen = ((int(m['month'].strftime('%m')), m['total'])
                                    for m in new_matches_by_month)

        resolved_matches_by_month_gen = ((int(m['month'].strftime('%m')), m['total'])
                                         for m in resolved_matches_by_month if m['month'])

        # Double-ended queue with all months abbreviated and a starting value
        full_year_of_months = deque([[month_abbr[x + 1], 0] for x in range(12)])

        for n in new_matches_by_month_gen:
            full_year_of_months[n[0] - 1][1] = n[1]  # Inserts the counted new matches

        for r in resolved_matches_by_month_gen:
            full_year_of_months[r[0] - 1][1] -= r[1]  # Subtracts the counted resolves

        # Rotate the current month to index 11
        current_month = int(current_date.strftime('%m'))
        full_year_of_months.rotate(-current_month)

        # Running total
        for i in range(11):  # Take value from current index and add it to the next
            full_year_of_months[i + 1][1] += full_year_of_months[i][1]

        return list(full_year_of_months)

    def count_new_matches_by_month(self, current_date):
        """Counts matches by months for the last year
        and rotates them by the current month"""
        a_year_ago = current_date - timedelta(days=365)

        # Truncates months with their match counts
        matches_by_month = self.matches.filter(
            created_timestamp__range=(a_year_ago, current_date)).annotate(
            month=TruncMonth('created_timestamp')).values(
            'month').annotate(
            total=Count('raw_matches')
        ).order_by('month')

        # Generator with the months as integers and the total
        matches_by_month_gen = ((int(m['month'].strftime('%m')), m['total'])
                                for m in matches_by_month)

        # Double-ended queue with all months abbreviated and a starting value
        deque_of_months = deque([[month_abbr[x + 1], 0] for x in range(12)])

        # Places totals from Generator to the correct months
        for m in matches_by_month_gen:
            deque_of_months[m[0] - 1][1] = m[1]

        # Rotates the current month to index 11
        current_month = int(current_date.strftime('%m'))
        deque_of_months.rotate(-current_month)

        return list(deque_of_months)


class LeaderStatisticsPageView(StatisticsPageView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['most_unhandled_employees'] = self.five_most_unhandled_employees()

        return context

    def five_most_unhandled_employees(self):
        counted_unhandled_matches_alias = self.unhandled_matches.values(
            'alias_relation__user__id').annotate(
            total=Count('raw_matches')).values(
                'alias_relation__user__first_name', 'total'
            ).order_by('-total')

        top_five = [[c['alias_relation__user__first_name'], c['total'], True]
                    for c in counted_unhandled_matches_alias][:5]

        for t in top_five:  # Finds and replaces 'None' with translated 'Not assigned'
            if t[0] is None:
                t[0], t[2] = _('Not assigned'), False

        # Sorted by counts, then alphabetically to make tests stable
        return sorted(top_five, key=lambda x: (-x[1], x[0]))

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if not user_is(Role.get_user_roles_or_default(request.user),
                           Leader):
                return HttpResponseForbidden()
        return super(LeaderStatisticsPageView, self).dispatch(
            request, *args, **kwargs)


class DPOStatisticsPageView(StatisticsPageView):

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if not user_is(Role.get_user_roles_or_default(request.user),
                           DataProtectionOfficer):
                return HttpResponseForbidden()
        return super(DPOStatisticsPageView, self).dispatch(
            request, *args, **kwargs)


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

    if user_is(roles, Remediator):
        unassigned_matches = Remediator(user=user).filter(matches)
        user_matches = DefaultRole(user=user).filter(matches)
        matches = unassigned_matches | user_matches
    else:
        matches = DefaultRole(user=user).filter(matches)

    return matches


def oidc_op_logout_url_method(request):
    logout_url = settings.LOGOUT_URL
    return_to_url = settings.LOGOUT_REDIRECT_URL
    return logout_url + '?' + urlencode({'redirect_uri': return_to_url,
                                         'client_id': settings.OIDC_RP_CLIENT_ID})
