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
from django.http import HttpResponseForbidden, Http404, HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.views.generic import View, TemplateView, ListView

from os2datascanner.utils.system_utilities import time_now
from os2datascanner.engine2.rules.cpr import CPRRule
from os2datascanner.engine2.rules.regex import RegexRule
from os2datascanner.engine2.rules.name import NameRule
from os2datascanner.engine2.rules.address import AddressRule
from os2datascanner.engine2.rules.links_follow import LinksFollowRule
from os2datascanner.engine2.rules.rule import Sensitivity
from os2datascanner.engine2.rules.wordlists import OrderedWordlistRule
from os2datascanner.projects.report.reportapp.models.roles.role import Role

from ..utils import user_is
from ..models.documentreport import DocumentReport
from ..models.roles.defaultrole import DefaultRole
from ..models.roles.remediator import Remediator
from ...organizations.models.account import Account

# For permissions
from ..models.roles.dpo import DataProtectionOfficer
from ..models.roles.leader import Leader

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = structlog.get_logger()

RENDERABLE_RULES = (
    CPRRule.type_label, RegexRule.type_label, LinksFollowRule.type_label,
    OrderedWordlistRule.type_label, NameRule.type_label, AddressRule.type_label
)


def user_is_superadmin(user):
    """Relevant users to notify if matches exist with
    the `only_notify_superuser`-flag."""
    roles = Role.get_user_roles_or_default(user)
    return (user_is(roles, DataProtectionOfficer)
            or user_is(roles, Leader) or user.is_superuser)


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
        resolution_status__isnull=True).order_by("sort_key", "pk")
    scannerjob_filters = None
    paginate_by_options = [10, 20, 50, 100, 250]

    def get_queryset(self):  # noqa CCR001
        user = self.request.user
        roles = Role.get_user_roles_or_default(user)
        # If called from a "distribute-matches"-button, remove all
        # `only_notify_superadmin`-flags from reports.
        is_htmx = self.request.headers.get("HX-Request") == "true"
        if is_htmx:
            htmx_trigger = self.request.headers.get("HX-Trigger-Name")

            # If called from a "open-button"-htmx link, update the last_opened_time value.
            if htmx_trigger == "open-button":
                DocumentReport.objects.get(pk=self.request.GET.get('pk')).update_opened()

        # Handles filtering by role + org and sets datasource_last_modified if non existing
        self.user_reports = filter_inapplicable_matches(user, self.document_reports, roles)
        self.document_reports = self.user_reports

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

    def get_context_data(self, **kwargs):  # noqa CCR001
        context = super().get_context_data(**kwargs)
        context["renderable_rules"] = RENDERABLE_RULES

        # Tell template if "distribute"-button should be visible
        context["distributable_matches"] = user_is_superadmin(
            self.request.user) and self.user_reports.filter(
            only_notify_superadmin=True).exists()

        context['undistributed_scannerjobs'] = self.user_reports.filter(  # noqa ECE001
                only_notify_superadmin=True).order_by(
                'scanner_job_pk').values(
                'scanner_job_pk').annotate(
                total=Count('scanner_job_pk')
                ).values(
                    'scanner_job_name', 'total', 'scanner_job_pk', 'scan_time'
                ).order_by('-scan_time')

        sensitivity_filter = Q(sensitivity=self.request.GET.get('sensitivities')
                               ) if self.request.GET.get('sensitivities') not in \
            ['all', None] else None
        scannerjob_filter = Q(scanner_job_pk=self.request.GET.get('scannerjob')
                              ) if self.request.GET.get('scannerjob') not in \
            ['all', None] else None

        if self.scannerjob_filters is None:
            # Create select options
            self.scannerjob_filters = self.user_reports.order_by(
                'scanner_job_pk').values(
                'scanner_job_pk').annotate(
                total=Count('scanner_job_pk', filter=sensitivity_filter)
                ).values(
                    'scanner_job_name', 'total', 'scanner_job_pk'
                )

        context['scannerjobs'] = (self.scannerjob_filters,
                                  self.request.GET.get('scannerjob', 'all'))

        context['30_days'] = self.request.GET.get('30-days', 'true')

        sensitivities = self.user_reports.order_by(
            '-sensitivity').values(
            'sensitivity').annotate(
            total=Count('sensitivity', filter=scannerjob_filter)
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

        is_htmx = self.request.headers.get('HX-Request') == "true"

        if is_htmx:
            htmx_trigger = self.request.headers.get('HX-Trigger-Name')
            if htmx_trigger == 'open-button':

                context['last_open_pk'] = self.request.GET.get('pk')

            # Serve the match fragment of the document report, that the user requested
            # more matches from. This could probably use a refactor.
            elif htmx_trigger == 'show-more-matches':

                # Increase number of shown matches
                last_index = int(self.request.GET.get('last_match') or 10)
                interval = [last_index, last_index + 10]
                context['interval'] = interval

                # Serve the fragments associated with the document report
                frags = self.document_reports.get(
                    pk=self.request.GET.get('dr_pk')).matches.matches
                for frag in frags:
                    if frag.rule.type_label in RENDERABLE_RULES:
                        context['frag'] = frag

                # Serve the document report key
                context['pk'] = self.request.GET.get('dr_pk')

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
        """Checks if a sort key is allowed and orders the queryset"""
        allowed_sorting_properties = ['sort_key', 'number_of_matches']
        if (sort_key := self.request.GET.get('order_by')) and (
                order := self.request.GET.get('order')):

            if sort_key not in allowed_sorting_properties:
                return

            if order != 'ascending':
                sort_key = '-'+sort_key
            self.document_reports = self.document_reports.order_by(sort_key, 'pk')

    def get_template_names(self):
        is_htmx = self.request.headers.get('HX-Request') == "true"
        htmx_trigger = self.request.headers.get('HX-Trigger-Name')
        if is_htmx:
            if htmx_trigger in [
                    'open-button',
                    'handle-matches-get',
                    'distribute-container',
                    'form-button',
                    'page-button',
                    'filter_form',
                    'dropdown_options',
                    'clear_scannerjob',
                    'clear_sensitivities']:
                return 'content.html'
            elif htmx_trigger in ['show-more-matches']:
                return 'components/matches_table.html'
        else:
            return 'index.html'

    def post(self, request, *args, **kwargs):

        is_htmx = request.headers.get("HX-Request", False) == "true"
        if is_htmx:
            htmx_trigger = request.headers.get("HX-Trigger-Name")
            if htmx_trigger == "distribute-matches":
                update_pks = request.POST.getlist('distribute-to')
                DocumentReport.objects.filter(
                    scanner_job_pk__in=update_pks).update(
                    only_notify_superadmin=False)
            elif htmx_trigger == "handle-matches":
                if Account.objects.filter(user=request.user).exists():
                    request.user.account.update_last_handle()
                DocumentReport.objects.filter(pk__in=self.request.POST.getlist(
                    'table-checkbox')).update(resolution_status=0)
            elif htmx_trigger == "handle-match":
                if Account.objects.filter(user=request.user).exists():
                    request.user.account.update_last_handle()
                self.document_reports.filter(
                    pk=self.request.POST.get('pk')).update(
                    resolution_status=0)

        response = HttpResponse()
        response.headers["HX-Trigger"] = "reload-htmx"

        return response


class StatisticsPageView(LoginRequiredMixin, TemplateView):
    context_object_name = "matches"  # object_list renamed to something more relevant
    model = DocumentReport
    users = Account.objects.all()
    matches = DocumentReport.objects.filter(
        raw_matches__matched=True)
    handled_matches = matches.filter(
        resolution_status__isnull=False)
    unhandled_matches = matches.filter(
        resolution_status__isnull=True)
    scannerjob_filters = None

    def get_template_names(self):
        is_htmx = self.request.headers.get('HX-Request') == 'true'
        if is_htmx:
            return "components/statistics-template.html"
        else:
            return "statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()
        if (scannerjob := self.request.GET.get('scannerjob')) and scannerjob != 'all':
            self.matches = self.matches.filter(
                scanner_job_pk=scannerjob)
            self.handled_matches = self.handled_matches.filter(
                scanner_job_pk=scannerjob)
            self.unhandled_matches = self.unhandled_matches.filter(
                scanner_job_pk=scannerjob)

        # Contexts are done as lists of tuples
        context['sensitivities'], context['total_matches'] = \
            self.count_all_matches_grouped_by_sensitivity()

        context['handled_matches'], context['total_handled_matches'] = \
            self.count_handled_matches_grouped_by_sensitivity()

        context['source_types'] = self.count_by_source_types()

        context['new_matches_by_month'] = self.count_new_matches_by_month(today)

        context['unhandled_matches_by_month'] = self.count_unhandled_matches_by_month(today)

        if self.scannerjob_filters is None:
            # Create select options
            self.scannerjob_filters = DocumentReport.objects.filter(
                raw_matches__matched=True).order_by('scanner_job_pk').values(
                "scanner_job_name", "scanner_job_pk").distinct()

        context['scannerjobs'] = (self.scannerjob_filters,
                                  self.request.GET.get('scannerjob', 'all'))

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
