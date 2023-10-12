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
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Count, Q
from django.http import Http404, HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View, ListView, DetailView

from os2datascanner.utils.system_utilities import time_now
from os2datascanner.engine2.rules.cpr import CPRRule
from os2datascanner.engine2.rules.experimental.cpr import TurboCPRRule
from os2datascanner.engine2.rules.experimental.health_rule import TurboHealthRule
from os2datascanner.engine2.rules.regex import RegexRule
from os2datascanner.engine2.rules.name import NameRule
from os2datascanner.engine2.rules.address import AddressRule
from os2datascanner.engine2.rules.links_follow import LinksFollowRule
from os2datascanner.engine2.rules.rule import Sensitivity
from os2datascanner.engine2.rules.wordlists import OrderedWordlistRule
from os2datascanner.engine2.rules.dict_lookup import EmailHeaderRule
from .view_utils import handle_report, delete_email
from ..models.documentreport import DocumentReport
from ...organizations.models.account import Account
from ...organizations.models.aliases import AliasType

logger = structlog.get_logger()

RENDERABLE_RULES = (
    CPRRule.type_label, RegexRule.type_label, LinksFollowRule.type_label,
    OrderedWordlistRule.type_label, NameRule.type_label, AddressRule.type_label,
    TurboCPRRule.type_label, EmailHeaderRule.type_label, TurboHealthRule.type_label,
)


class EmptyPagePaginator(Paginator):
    def validate_number(self, number):
        try:
            return super(EmptyPagePaginator, self).validate_number(number)
        except EmptyPage:
            if number > 1:
                return self.num_pages
            else:
                raise Http404(_('The page does not exist'))


class ReportView(LoginRequiredMixin, ListView):
    template_name = 'index.html'
    paginator_class = EmptyPagePaginator
    paginate_by = 10
    context_object_name = 'document_reports'
    model = DocumentReport
    scannerjob_filters = None
    paginate_by_options = [10, 20, 50, 100, 250]

    document_reports = DocumentReport.objects.filter(
            number_of_matches__gte=1,
            resolution_status__isnull=True).order_by(
            'sort_key',
            'pk')

    def get_queryset(self):
        self.document_reports = self.base_match_filter(self.document_reports)
        self.all_reports = self.document_reports

        self.apply_filters()
        self.order_queryset_by_property()

        return self.document_reports.only(
            "name",
            "resolution_status",
            "resolution_time",
            "last_opened_time",
            "raw_matches",
            "datasource_last_modified",
            "raw_problem"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["renderable_rules"] = RENDERABLE_RULES
        context["resolution_choices"] = DocumentReport.ResolutionChoices.choices
        self.add_form_context(context)
        return context

    def base_match_filter(self, reports):
        """Base filtering of document reports. Extended in children views."""
        try:
            if user_org := self.request.user.account.organization:
                reports = reports.filter(organization=user_org)
            else:
                reports = DocumentReport.objects.none()
        except Account.DoesNotExist as e:
            logger.warning(f"While trying to apply base match filter for user "
                           f"{self.request.user}, the following error occurred: {e}. "
                           "Returning no document reports for user.")
            reports = DocumentReport.objects.none()

        return reports

    def apply_filters(self):
        if self.request.GET.get('30-days') == 'false':
            older_than_30 = time_now() - timedelta(days=30)
            self.document_reports = self.document_reports.filter(
                datasource_last_modified__lte=older_than_30)

        if (scannerjob := self.request.GET.get('scannerjob')) and scannerjob != 'all':
            self.document_reports = self.document_reports.filter(
                scanner_job_pk=int(scannerjob))

        if (sensitivity := self.request.GET.get('sensitivities')) and sensitivity != 'all':
            self.document_reports = self.document_reports.filter(sensitivity=int(sensitivity))

        if (method := self.request.GET.get('resolution_status')) and method != 'all':
            self.document_reports = self.document_reports.filter(resolution_status=int(method))

        if (source_type := self.request.GET.get('source_type')) and source_type != 'all':
            self.document_reports = self.document_reports.filter(source_type=source_type)

    def order_queryset_by_property(self):
        """Checks if a sort key is allowed and orders the queryset"""
        allowed_sorting_properties = [
            'sort_key',
            'number_of_matches',
            'resolution_status',
            'datasource_last_modified']
        if (sort_key := self.request.GET.get('order_by')) and (
                order := self.request.GET.get('order')):

            if sort_key not in allowed_sorting_properties:
                return

            if order != 'ascending':
                sort_key = '-'+sort_key
            self.document_reports = self.document_reports.order_by(sort_key, 'pk')

    def add_form_context(self, context):
        sensitivity_filter = Q(sensitivity=self.request.GET.get('sensitivities')
                               ) if self.request.GET.get('sensitivities') not in \
            ['all', None] else Q()
        scannerjob_filter = Q(scanner_job_pk=self.request.GET.get('scannerjob')
                              ) if self.request.GET.get('scannerjob') not in \
            ['all', None] else Q()
        resolution_status_filter = Q(resolution_status=self.request.GET.get(
            'resolution_status')) if self.request.GET.get('resolution_status') not in \
            ['all', None] else Q()

        if self.scannerjob_filters is None:
            # Create select options
            self.scannerjob_filters = self.all_reports.order_by(
                'scanner_job_pk').values(
                'scanner_job_pk').annotate(
                filtered_total=Count('scanner_job_pk',
                                     filter=sensitivity_filter & resolution_status_filter),
                total=Count('scanner_job_pk')
                ).values(
                    'scanner_job_name', 'total', 'filtered_total', 'scanner_job_pk'
                )

        context['scannerjobs'] = (self.scannerjob_filters,
                                  self.request.GET.get('scannerjob', 'all'))

        context['30_days'] = self.request.GET.get('30-days', 'true')

        sensitivities = self.all_reports.order_by(
                '-sensitivity').values(
                'sensitivity').annotate(
                total=Count('sensitivity', filter=scannerjob_filter & resolution_status_filter)
            ).values(
                'sensitivity', 'total'
            )

        context['sensitivities'] = (((Sensitivity(s["sensitivity"]),
                                    s["total"]) for s in sensitivities),
                                    self.request.GET.get('sensitivities', 'all'))

        context['source_types'] = (self.all_reports.order_by("source_type").values(
            "source_type"
        ).annotate(
            total=Count("source_type", filter=sensitivity_filter & scannerjob_filter),
        ).values("source_type", "total"),
                                   self.request.GET.get('source_type', 'all'))

        resolution_status = self.all_reports.order_by(
                'resolution_status').values(
                'resolution_status').annotate(
                total=Count('resolution_status', filter=sensitivity_filter & scannerjob_filter),
                ).values('resolution_status', 'total',
                         )

        for method in resolution_status:
            method['resolution_label'] = DocumentReport.ResolutionChoices(
                method['resolution_status']).label if method['resolution_status'] \
                or method['resolution_status'] == 0 else None

        context['resolution_status'] = (
            resolution_status, self.request.GET.get(
                'resolution_status', 'all'))

        context['paginate_by'] = int(self.request.GET.get('paginate_by', self.paginate_by))
        context['paginate_by_options'] = self.paginate_by_options

        context['order_by'] = self.request.GET.get('order_by', 'sort_key')
        context['order'] = self.request.GET.get('order', 'ascending')

    def get_paginate_by(self, queryset):
        # Overrides get_paginate_by to allow changing it in the template
        # as url param paginate_by=xx
        return self.request.GET.get('paginate_by', self.paginate_by)


class UserReportView(ReportView):
    """Presents the user with their personal unhandled results."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["personal"] = True
        return context

    def base_match_filter(self, reports):
        reports = super().base_match_filter(reports)
        # Find everything alias related, not withheld and not remediator related.
        reports = reports.filter(
            alias_relation__in=self.request.user.aliases.exclude(_alias_type=AliasType.REMEDIATOR),
            only_notify_superadmin=False)
        return reports


class RemediatorView(ReportView):
    """Presents a remediator with relevant unhandled results."""

    def base_match_filter(self, reports):
        reports = super().base_match_filter(reports)
        # Find everything remediator related and not withheld
        reports = reports.filter(
            alias_relation__in=self.request.user.aliases.filter(_alias_type=AliasType.REMEDIATOR),
            only_notify_superadmin=False)
        return reports

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        try:
            if request.user.account.is_remediator or request.user.is_superuser:
                return response
        except Exception as e:
            logger.warning("Exception raised while trying to dispatch to user "
                           f"{request.user}: {e}")
        return redirect(reverse_lazy('index'))


class UndistributedView(ReportView):
    """Presents a superuser with all undistributed unhandled results."""

    def base_match_filter(self, reports):
        reports = super().base_match_filter(reports)
        reports = reports.filter(only_notify_superadmin=True)
        return reports

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['undistributed_scannerjobs'] = self.scannerjob_filters
        return context

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        try:
            if request.user.is_superuser:
                return response
        except Exception as e:
            logger.warning("Exception raised while trying to dispatch to user "
                           f"{request.user}: {e}")
        return redirect(reverse_lazy('index'))


class ArchiveMixin:
    """This mixin is able to overwrite some logic on children of the ReportView-
    class, most notably changing the queryset to query for handled results
    instead of unhandled results."""

    document_reports = DocumentReport.objects.filter(
            number_of_matches__gte=1,
            resolution_status__isnull=False).order_by(
            'sort_key',
            'pk')

    def dispatch(self, request, *args, **kwargs):
        if settings.ARCHIVE_TAB:
            return super().dispatch(request, *args, **kwargs)
        else:
            return redirect(reverse_lazy('index'))


class UserArchiveView(ArchiveMixin, UserReportView):
    """Presents the user with their personal handled results."""


class RemediatorArchiveView(ArchiveMixin, RemediatorView):
    """Presents the remediator with all relevant handled results."""


class UndistributedArchiveView(ArchiveMixin, UndistributedView):
    """Presents a superuser with all undistributed handled results."""


class HTMXEndpointView(LoginRequiredMixin, View):
    """A view for sending POST-requests via HTMX to the backend."""

    model = DocumentReport

    def post(self, request, *args, **kwargs):

        # Add a header value to the response before returning to initiate reload of some elements.
        response = HttpResponse()
        response.headers["HX-Trigger"] = "reload-htmx"

        return response

    def dispatch(self, request, *args, **kwargs):
        self.is_htmx = request.headers.get('HX-Request')
        if self.is_htmx == "true":
            return super().dispatch(request, *args, **kwargs)
        else:
            return Http404()


class HandleMatchView(HTMXEndpointView, DetailView):
    """Endpoint for handling matches via HTMX."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        report = self.get_object()
        action = request.POST.get('action')
        handle_report(self.request.user.account, report, action)

        return response


class MassHandleView(HTMXEndpointView, ListView):
    """Endpoint for mass handling matches via HTMX."""

    def get_queryset(self):
        qs = super().get_queryset()
        pks = self.request.POST.getlist("table-checkbox", [])
        reports = qs.filter(pk__in=pks)
        return reports

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        reports = self.get_queryset()
        action = request.POST.get('action')
        self.handle_reports(reports, action)

        return response

    def handle_reports(self, reports, action):
        try:
            self.request.user.account.update_last_handle()
        except Exception as e:
            logger.warning("Exception raised while trying to update last_handle field "
                           f"of account belonging to user {self.request.user}:", e)

        for report in reports:
            report.resolution_status = action
            report.raw_problem = None
            report.save()
        logger.info(
            f"Successfully handled DocumentReports "
            f"{', '.join([str(report) for report in reports])} with "
            f"resolution_status {action}.")


class OpenMatchView(HTMXEndpointView, DetailView):
    """Endpoint for marking matches as opened."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        report = self.get_object()

        report.update_opened()

        request.session["last_opened"] = str(report.pk)

        return response


class ShowMoreMatchesView(HTMXEndpointView, DetailView):
    template_name = "components/matches_table.html"
    model = DocumentReport

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Increase number of shown matches
        last_index = int(self.request.GET.get('last_match', '10'))
        interval = [last_index, last_index + 10]
        context['interval'] = interval

        # Serve the fragments associated with the document report
        frags = self.object.matches.matches
        for frag in frags:
            if frag.rule.type_label in RENDERABLE_RULES:
                context['frag'] = frag

        # Serve the document report key
        context['pk'] = self.object.pk

        return context


class DistributeMatchesView(HTMXEndpointView, ListView):
    model = DocumentReport

    def get_queryset(self):
        qs = super().get_queryset()
        scanner_job_pk = self.request.POST.get('distribute-to')
        qs = qs.filter(scanner_job_pk=scanner_job_pk)
        return qs

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        object_list = self.get_queryset()

        update_output = object_list.update(only_notify_superadmin=False)

        logger.info(f"Updated DocumetReport objects: {update_output}")

        return response


class DeleteMailView(HTMXEndpointView, DetailView):
    """ View for sending a delete request for one email
    through the MSGraph message API. """
    model = DocumentReport

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        report = self.get_object()

        try:
            delete_email(report, request.user.account)
        except PermissionDenied as e:
            error_message = _("Failed to delete {pn}: {e}").format(
                pn=report.matches.handle.presentation_name, e=e)
            messages.add_message(
                request,
                messages.WARNING,
                error_message)
        return response


class MassDeleteMailView(HTMXEndpointView, ListView):
    """ View for sending delete requests for multiple emails
     through the MSGraph message API. """

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        reports = self.get_queryset()
        self.delete_emails(reports)

        return response

    def get_queryset(self):
        qs = super().get_queryset()
        pks = self.request.POST.getlist("table-checkbox", [])
        reports = qs.filter(pk__in=pks)
        return reports

    def delete_emails(self, document_reports):
        for report in document_reports:
            try:
                delete_email(report, self.request.user.account)
            except PermissionDenied as e:
                error_message = _("Failed to delete {pn}: {e}").format(
                    pn=report.matches.handle.presentation_name, e=e)
                messages.add_message(
                    self.request,
                    messages.WARNING,
                    error_message)
