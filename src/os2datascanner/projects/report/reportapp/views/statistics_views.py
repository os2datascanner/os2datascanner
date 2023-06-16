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

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count, DateField
from django.db.models.functions import Coalesce, TruncMonth
from django.http import HttpResponseForbidden, Http404, HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.views.generic import TemplateView, DetailView
from django.shortcuts import get_object_or_404

from os2datascanner.utils.system_utilities import time_now
from os2datascanner.engine2.rules.rule import Sensitivity
from os2datascanner.projects.report.reportapp.models.roles.role import Role

from ..models.documentreport import DocumentReport
from ...organizations.models.account import Account
from ...organizations.models.organizational_unit import OrganizationalUnit
from ..utils import user_is, user_is_superadmin
from ..models.roles.defaultrole import DefaultRole
from ..models.roles.remediator import Remediator

# For permissions
from ..models.roles.dpo import DataProtectionOfficer

logger = structlog.get_logger()


class StatisticsPageView(LoginRequiredMixin, TemplateView):
    context_object_name = "matches"  # object_list renamed to something more relevant
    template_name = "statistics.html"
    model = DocumentReport
    users = Account.objects.all()
    matches = DocumentReport.objects.filter(
        number_of_matches__gte=1)
    handled_matches = matches.filter(
        resolution_status__isnull=False)
    unhandled_matches = matches.filter(
        resolution_status__isnull=True)
    scannerjob_filters = None

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

        context['handled_matches_status'] = \
            self.count_handles_matches_grouped_by_resolution_status()

        if self.scannerjob_filters is None:
            # Create select options
            self.scannerjob_filters = DocumentReport.objects.filter(
                number_of_matches__gte=1).order_by('scanner_job_pk').values(
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

    def count_handles_matches_grouped_by_resolution_status(self):
        """Counts the distribution of handled matches grouped by resolution_status"""
        handled_matches = self.handled_matches.order_by(
            'resolution_status').values(
            'resolution_status').annotate(
            total=Count('resolution_status')
            ).values(
                'resolution_status', 'total'
            )

        return self.create_resolution_status_list(handled_matches)

    def create_sensitivity_list(self, matches):
        """Helper method which groups the totals by sensitivities
        and also takes the sum of the totals"""
        # For handling having no values - List defaults to 0
        sensitivity_list = [
            [Sensitivity.CRITICAL.presentation, 0],
            [Sensitivity.PROBLEM.presentation, 0],
            [Sensitivity.WARNING.presentation, 0],
            [Sensitivity.NOTICE.presentation, 0]
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

    def create_resolution_status_list(self, matches):
        """Helper method which groups the totals by resolution_status
        and also takes the sum of the totals."""
        resolution_list = [
            [choice[0], choice[1], 0] for choice in DocumentReport.ResolutionChoices.choices
        ]

        for match in matches:
            for status in resolution_list:
                if match['resolution_status'] == status[0]:
                    status[2] = match['total']
                    break

        # Sum of the totals
        total = 0
        for match in resolution_list:
            total += match[2]

        return resolution_list, total

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
            month=TruncMonth(
                    'created_timestamp', output_field=DateField())).values(
            'month').annotate(
            total=Count('raw_matches')
        ).order_by('month')

        resolved_matches_by_month = self.handled_matches.filter(
            created_timestamp__range=(a_year_ago, current_date)).annotate(
            month=TruncMonth(
                    # If resolution_time isn't set on a report that has been
                    # handled, then assume it was handled in the same month it
                    # was created
                    Coalesce('resolution_time', 'created_timestamp'),
                    output_field=DateField())).values(
            'month').annotate(
            total=Count('raw_matches')
        ).order_by('month')

        # Generators with months as integers and the counts
        new_matches_by_month_gen = ((m['month'].month, m['total'])
                                    for m in new_matches_by_month)

        resolved_matches_by_month_gen = ((m['month'].month, m['total'])
                                         for m in resolved_matches_by_month)

        values_by_month = [0] * 12

        for month_id, total in new_matches_by_month_gen:
            values_by_month[month_id - 1] += total

        for month_id, total in resolved_matches_by_month_gen:
            values_by_month[month_id - 1] -= total

        # month_abbr[0] is the empty string, which makes it possible to do
        # month_abbr(dt.month) without thinking about indexes -- but that's
        # slightly inconvenient for us
        labelled_values_by_month = deque(
                list(k) for k in zip(month_abbr[1:], values_by_month))
        # Rotate the current month to index 11
        labelled_values_by_month.rotate(-current_date.month)

        # Running total
        for i in range(11):  # Take value from current index and add it to the next
            labelled_values_by_month[i + 1][1] += labelled_values_by_month[i][1]

        return list(labelled_values_by_month)

    def count_new_matches_by_month(self, current_date):
        """Counts matches by months for the last year
        and rotates them by the current month"""
        a_year_ago = current_date - timedelta(days=365)

        # Truncates months with their match counts
        matches_by_month = self.matches.filter(
            created_timestamp__range=(a_year_ago, current_date)).annotate(
            month=TruncMonth(
                    'created_timestamp', output_field=DateField())).values(
            'month').annotate(
            total=Count('raw_matches')
        ).order_by('month')
        # A QuerySet of objects, one for each month, of the form
        # {'month': datetime.date(2023, 1, 1), 'total': 11117}

        # Generator with the months as integers and the total
        matches_by_month_gen = ((m['month'].month, m['total'])
                                for m in matches_by_month)

        values_by_month = [0] * 12

        for month_id, total in matches_by_month_gen:
            values_by_month[month_id - 1] += total

        labelled_values_by_month = deque(
                list(k) for k in zip(month_abbr[1:], values_by_month))
        # Rotates the current month to index 11
        labelled_values_by_month.rotate(-current_date.month)

        return list(labelled_values_by_month)


class LeaderStatisticsPageView(LoginRequiredMixin, TemplateView):
    template_name = "statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_superuser:
            user_units = OrganizationalUnit.objects.all()
        else:
            user_units = OrganizationalUnit.objects.filter(
                Q(positions__account=self.request.user.account) & Q(positions__role="manager"))

        context['user_units'] = user_units

        if unit_uuid := self.request.GET.get('org_unit', None):
            org_unit = user_units.get(uuid=unit_uuid)
        else:
            org_unit = user_units.first() or None
        context["org_unit"] = org_unit

        if org_unit:
            accounts = Account.objects.filter(units=org_unit)
            if search_field := self.request.GET.get('search_field', None):
                self.employees = accounts.filter(
                    Q(first_name__icontains=search_field) |
                    Q(last_name__icontains=search_field) |
                    Q(username__istartswith=search_field))
            else:
                self.employees = accounts
            self.order_employees()
            # This operation should NOT be done here. Move this to somehwere it makes sense.
            for employee in self.employees:
                employee.save()
        else:
            self.employees = None
        context["employees"] = self.employees

        context['order_by'] = self.request.GET.get('order_by', 'first_name')
        context['order'] = self.request.GET.get('order', 'ascending')

        return context

    def order_employees(self):
        """Checks if a sort key is allowed and orders the employees queryset"""
        allowed_sorting_properties = [
            'first_name',
            'match_count',
            'match_status']
        if (sort_key := self.request.GET.get('order_by', 'first_name')) and (
                order := self.request.GET.get('order', 'ascending')):

            if sort_key not in allowed_sorting_properties:
                return

            if order != 'ascending':
                sort_key = '-'+sort_key
            self.employees = self.employees.order_by(sort_key, 'pk').distinct(
                sort_key if sort_key[0] != "-" else sort_key[1:], "pk")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if not request.user.is_superuser and not request.user.account.is_manager:
                return HttpResponseForbidden(
                    "Only managers and superusers have access to this page.")
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


class UserStatisticsPageView(LoginRequiredMixin, DetailView):
    template_name = "statistics.html"
    model = Account
    context_object_name = "account"

    def get_object(self, queryset=None):
        if self.kwargs.get(self.pk_url_kwarg) is None:
            try:
                self.kwargs[self.pk_url_kwarg] = self.request.user.account.uuid
            except Account.DoesNotExist:
                raise Http404()
        return super().get_object(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        account = context["account"]
        matches_by_week = account.count_matches_by_week()
        context["matches_by_week"] = matches_by_week
        scannerjobs = filter_inapplicable_matches(
            account.user,
            DocumentReport.objects.filter(
                number_of_matches__gte=1,
                resolution_status__isnull=True
            ),
            Role.get_user_roles_or_default(account.user)
            ).order_by(
                "scanner_job_pk"
            ).values(
                "scanner_job_pk",
                "scanner_job_name"
            ).annotate(
                total=Count("scanner_job_pk")
            ).values(
                "scanner_job_pk",
                "scanner_job_name",
                "total"
            )
        context["scannerjobs"] = scannerjobs
        return context

    def post(self, request, *args, **kwargs):

        pk = kwargs.get("pk")
        self.verify_access(request.user, pk)

        scannerjob_pk = request.POST.get("pk")
        scannerjob_name = request.POST.get("name")
        account = Account.objects.get(pk=pk)

        reports = filter_inapplicable_matches(
            account.user,
            DocumentReport.objects.filter(
                scanner_job_pk=scannerjob_pk,
                resolution_status__isnull=True,
                number_of_matches__gte=1),
            Role.get_user_roles_or_default(
                account.user))

        response_string = _('You deleted all results from {0} associated with {1}.'.format(
                scannerjob_name, account.get_full_name()))

        reports.delete()

        response = HttpResponse(
            "<li>" +
            response_string +
            "</li>")

        response.headers["HX-Trigger"] = "reload-htmx"
        return response

    def get(self, request, *args, **kwargs):
        try:
            # If the URL has specified a primary key for the Account whose
            # statistics we want to see, then use that
            pk = kwargs.get("pk") or request.user.account.pk
        except Account.DoesNotExist:
            raise Http404()

        self.verify_access(request.user, pk)

        return super().get(request, *args, **kwargs)

    def verify_access(self, user, pk):
        target_account = get_object_or_404(Account, pk=pk)
        try:
            user_account = user.account
        except Account.DoesNotExist:
            user_account = None

        # (Note that accessing Account.user can't raise a DoesNotExist in the
        # way that User.account can, so we don't need to wrap this line)
        owned = target_account.user == user
        managed = user_account and target_account.managed_by(user_account)

        if user.is_superuser or owned or managed:
            return
        else:
            raise PermissionDenied

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
