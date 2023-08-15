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

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from calendar import month_abbr
from collections import deque

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count, DateField
from django.db.models.functions import Coalesce, TruncMonth
from django.http import HttpResponseForbidden, Http404, HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.views.generic import TemplateView, DetailView, ListView
from django.shortcuts import get_object_or_404

from os2datascanner.projects.report.reportapp.models.roles.role import Role

from ..models.documentreport import DocumentReport
from ...organizations.models.account import Account
from ...organizations.models.organizational_unit import OrganizationalUnit
from ..utils import user_is, user_is_superadmin
from ..models.roles.defaultrole import DefaultRole
from ..models.roles.remediator import Remediator
from .report_views import EmptyPagePaginator

# For permissions
from ..models.roles.dpo import DataProtectionOfficer


logger = structlog.get_logger()


def month_delta(series_start: date, here: date):
    """Returns the (zero-based) month index of @here relative to
    @series_start."""

    def _months(date: date):
        return date.year * 12 + date.month

    return _months(here) - _months(series_start)


class DPOStatisticsPageView(LoginRequiredMixin, TemplateView):
    context_object_name = "matches"  # object_list renamed to something more relevant
    template_name = "statistics.html"
    model = DocumentReport
    scannerjob_filters = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.matches = DocumentReport.objects.filter(
            number_of_matches__gte=1).annotate(
            created_month=TruncMonth('created_timestamp', output_field=DateField()),
            resolved_month=TruncMonth(
                        # If resolution_time isn't set on a report that has been
                        # handled, then assume it was handled in the same month it
                        # was created
                        Coalesce('resolution_time', 'created_timestamp'),
                        output_field=DateField())).values(
                            'resolution_status',
                            'source_type',
                            'created_month',
                            'resolved_month'
                        ).annotate(count=Count('source_type')).order_by()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()
        if (scannerjob := self.request.GET.get('scannerjob')) and scannerjob != 'all':
            self.matches = self.matches.filter(
                scanner_job_pk=scannerjob)

        if (orgunit := self.request.GET.get('orgunit')) and orgunit != '--':
            self.matches = self.matches.filter(
                alias_relation__account__units=orgunit)

        if self.scannerjob_filters is None:
            # Create select options
            self.scannerjob_filters = DocumentReport.objects.filter(
                number_of_matches__gte=1).order_by('scanner_job_pk').values(
                "scanner_job_name", "scanner_job_pk").distinct()

        (context['match_data'],
         context['source_types'],
         context['resolution_status'],
         self.created_month,
         self.resolved_month) = self.make_data_structures(self.matches)

        context['unhandled_matches_by_month'] = self.count_unhandled_matches_by_month(today)

        context['new_matches_by_month'] = self.count_new_matches_by_month(today)

        context['scannerjobs'] = (self.scannerjob_filters,
                                  self.request.GET.get('scannerjob', 'all'))

        allowed_orgunits = OrganizationalUnit.objects.all() if self.request.user.is_superuser \
            else OrganizationalUnit.objects.filter(
                    organization=self.request.user.account.organization)

        context['orgunits'] = (allowed_orgunits.order_by("name").values("name", "uuid"),
                               self.request.GET.get('orgunit', 'all'))

        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if not user_is(Role.get_user_roles_or_default(request.user),
                           DataProtectionOfficer):
                return HttpResponseForbidden()
            # Only allow the user to see reports from their own organization
            if not request.user.is_superuser:
                org = request.user.account.organization
                self.matches = self.matches.filter(organization=org)
        return super().dispatch(
            request, *args, **kwargs)

    def make_data_structures(self, matches):  # noqa C901, CCR001
        """To avoid making multiple separate queries to the DocumentReport
        table, we instead use the one call defined previously, then packages
        data into separate structures, which can then be used for statistical
        presentations."""

        match_data = {
            'handled': 0,
            'unhandled': 0
        }

        resolution_status = {choice.value: {"label": choice.label, "count": 0}
                             for choice in DocumentReport.ResolutionChoices}

        source_type = {
            'other': {'count': 0, 'label': _('Other')},
            'webscan': {'count': 0, 'label': _('Webscan')},
            'filescan': {'count': 0, 'label': _('Filescan')},
            'mailscan': {'count': 0, 'label': _('Mailscan')}
        }

        created_month = {}

        resolved_month = {}

        for obj in matches:
            match obj:
                case {"source_type": "smb" | "smbc", "count": count}:
                    source_type["filescan"]["count"] += count
                case {"source_type": "web", "count": count}:
                    source_type["webscan"]["count"] += count
                case {"source_type": "ews" | "msgraph-mail", "count": count}:
                    source_type["mailscan"]["count"] += count
                case {"count": count}:
                    source_type["other"]["count"] += count

            match obj:
                case {"resolution_status": None, "count": count}:
                    match_data["unhandled"] += count
                case {"resolution_status": val, "count": count}:
                    match_data["handled"] += count
                    resolution_status[val]["count"] += count

            created_month[obj["created_month"]] = created_month.get(
                obj["created_month"], 0) + obj["count"]
            if obj["resolution_status"] is not None:
                resolved_month[obj["resolved_month"]] = resolved_month.get(
                    obj["resolved_month"], 0) + obj["count"]

        return match_data, source_type, resolution_status, created_month, resolved_month

    def count_unhandled_matches_by_month(self, current_date):
        """Counts new matches and resolved matches by month for the last year,
        rotates the current month to the end of the list, inserts and subtracts using the counts
        and then makes a running total"""
        a_year_ago: date = (
                current_date - timedelta(days=365)).date().replace(day=1)

        new_matches_by_month = sort_by_keys(self.created_month)

        resolved_matches_by_month = sort_by_keys(self.resolved_month)

        if self.matches.exists():
            earliest_month = min(
                    key
                    for key in new_matches_by_month.keys() | resolved_matches_by_month.keys())
            # The range of the graph should be at least a year
            earliest_month = min(earliest_month, a_year_ago)
        else:
            # ... even if we don't have /any/ data at all
            earliest_month = a_year_ago
        number_of_months = 1 + month_delta(earliest_month, current_date)

        # This series needs to have a slot for every month, not just those in
        # which something actually happened
        delta_by_month: dict[date, int] = {
                earliest_month + relativedelta(months=k): 0
                for k in range(number_of_months)}

        for month, total in new_matches_by_month.items():
            delta_by_month[month] += total
        for month, total in resolved_matches_by_month.items():
            delta_by_month[month] -= total

        def _make_running_total():
            total = 0
            for month_start, delta in delta_by_month.items():
                total += delta
                yield month_start, total

        return [[month_abbr[month_start.month], total]
                for month_start, total in list(_make_running_total())[-12:]]

    def count_new_matches_by_month(self, current_date):
        """Counts matches by months for the last year
        and rotates them by the current month"""
        a_year_ago = current_date - timedelta(days=365)

        matches_by_month = sort_by_keys(self.created_month)

        # We only want data from the last 12 months
        cutoff_day = timezone.make_aware(
            timezone.datetime(
                a_year_ago.year,
                a_year_ago.month+1,
                1)).date()
        earlier_months = [month for month in matches_by_month.keys() if month < cutoff_day]
        for month in earlier_months:
            del matches_by_month[month]

        # Generator with the months as integers and the total
        matches_by_month_gen = ((month.month, total)
                                for month, total in matches_by_month.items())

        values_by_month = [0] * 12

        for month_id, total in matches_by_month_gen:
            values_by_month[month_id - 1] += total

        labelled_values_by_month = deque(
                list(k) for k in zip(month_abbr[1:], values_by_month))
        # Rotates the current month to index 11
        labelled_values_by_month.rotate(-current_date.month)

        return list(labelled_values_by_month)


class LeaderStatisticsPageView(LoginRequiredMixin, ListView):
    template_name = "statistics.html"
    paginator_class = EmptyPagePaginator
    paginate_by = 200
    model = Account
    context_object_name = "employees"

    def get_queryset(self):
        qs = super().get_queryset()

        if self.org_unit:
            qs = qs.filter(units=self.org_unit)
        else:
            qs = Account.objects.none()

        self.employee_count = qs.count()

        if search_field := self.request.GET.get('search_field', None):
            qs = qs.filter(
                Q(first_name__icontains=search_field) |
                Q(last_name__icontains=search_field) |
                Q(username__istartswith=search_field))

        qs = self.order_employees(qs)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['user_units'] = self.user_units

        context["org_unit"] = self.org_unit

        context["employee_count"] = self.employee_count

        context['order_by'] = self.request.GET.get('order_by', 'first_name')
        context['order'] = self.request.GET.get('order', 'ascending')

        return context

    def order_employees(self, qs):
        """Checks if a sort key is allowed and orders the employees queryset"""
        allowed_sorting_properties = [
            'first_name',
            'match_count',
            'match_status']
        if (sort_key := self.request.GET.get('order_by', 'first_name')) and (
                order := self.request.GET.get('order', 'ascending')):

            if sort_key not in allowed_sorting_properties:
                return

            if sort_key == "match_count":
                # Trigger recomputation of match_count by saving
                # all the objects again. FIXME FIXME FIXME!!!
                for acc in qs:
                    acc.save()

            if order != 'ascending':
                sort_key = '-'+sort_key
            qs = qs.order_by(sort_key, 'pk').distinct(
                sort_key if sort_key[0] != "-" else sort_key[1:], "pk")

        return qs

    def get(self, request, *args, **kwargs):
        if self.request.user.is_superuser:
            self.user_units = OrganizationalUnit.objects.all().order_by("name")
        else:
            self.user_units = (OrganizationalUnit.objects.filter(
                Q(positions__account=self.request.user.account) & Q(positions__role="manager"))
                .order_by("name"))

        if unit_uuid := request.GET.get('org_unit', None):
            self.org_unit = self.user_units.get(uuid=unit_uuid)
        else:
            self.org_unit = self.user_units.first() or None

        response = super().get(request, *args, **kwargs)

        return response

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if not request.user.is_superuser and not request.user.account.is_manager:
                return HttpResponseForbidden(
                    "Only managers and superusers have access to this page.")
        return super(LeaderStatisticsPageView, self).dispatch(
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


class EmployeeView(LoginRequiredMixin, DetailView):
    model = Account
    context_object_name = "employee"
    template_name = "components/employee_template.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        self.object.save()
        return response

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


def sort_by_keys(d: dict) -> dict:
    return dict(sorted(d.items(), key=lambda t: t[0]))
