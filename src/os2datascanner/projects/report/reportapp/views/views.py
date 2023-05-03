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
from urllib.parse import urlencode
from django.conf import settings

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import Http404, HttpResponse
from django.utils.translation import ugettext_lazy as _
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

from ..utils import user_is, user_is_superadmin
from ..models.documentreport import DocumentReport
from ..models.roles.defaultrole import DefaultRole
from ..models.roles.remediator import Remediator
from ...organizations.models.account import Account

# For permissions

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

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


class MainPageView(LoginRequiredMixin, ListView):
    template_name = 'index.html'
    paginator_class = EmptyPagePaginator
    paginate_by = 10  # Determines how many objects pr. page.
    context_object_name = "document_reports"  # object_list renamed to something more relevant
    model = DocumentReport
    document_reports = DocumentReport.objects.filter(
        number_of_matches__gte=1).filter(
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

        # Apply filters to the queryset based on options chosen by the user.
        self.apply_filters()

        return self.document_reports.only(
            "name",
            "resolution_status",
            "resolution_time",
            "last_opened_time",
            "raw_matches")

    def get_context_data(self, **kwargs):  # noqa CCR001
        context = super().get_context_data(**kwargs)
        context["renderable_rules"] = RENDERABLE_RULES
        context["resolution_choices"] = DocumentReport.ResolutionChoices.choices

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

        # Add context for populating the filter options.
        self.add_form_context(context)

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
        allowed_sorting_properties = ['sort_key', 'number_of_matches', 'resolution_status']
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
            self.scannerjob_filters = self.user_reports.order_by(
                'scanner_job_pk').values(
                'scanner_job_pk').annotate(
                total=Count('scanner_job_pk', filter=sensitivity_filter & resolution_status_filter)
                ).values(
                    'scanner_job_name', 'total', 'scanner_job_pk'
                )

        context['scannerjobs'] = (self.scannerjob_filters,
                                  self.request.GET.get('scannerjob', 'all'))

        context['30_days'] = self.request.GET.get('30-days', 'true')

        sensitivities = self.user_reports.order_by(
                '-sensitivity').values(
                'sensitivity').annotate(
                total=Count('sensitivity', filter=scannerjob_filter & resolution_status_filter)
            ).values(
                'sensitivity', 'total'
            )

        context['sensitivities'] = (((Sensitivity(s["sensitivity"]),
                                    s["total"]) for s in sensitivities),
                                    self.request.GET.get('sensitivities', 'all'))

        resolution_status = self.user_reports.order_by(
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

    def apply_filters(self):
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

        if (method := self.request.GET.get('resolution_status')) and method != 'all':
            self.document_reports = self.document_reports.filter(resolution_status=int(method))

        self.order_queryset_by_property()

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
                    'clear_sensitivities',
                    'clear_resolution_status',
                    'revert-match',
                    'revert-matches']:
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
                DocumentReport.objects.filter(
                    pk__in=self.request.POST.getlist('table-checkbox')).update(
                    resolution_status=self.request.POST.get(
                        'action', 0), resolution_time=time_now())
            elif htmx_trigger == "handle-match":
                if Account.objects.filter(user=request.user).exists():
                    request.user.account.update_last_handle()
                report = self.document_reports.get(
                    pk=self.request.POST.get('pk'))
                report.resolution_status = self.request.POST.get('action', 0)
                report.save()

        # Add a header value to the response before returning to initiate reload of some elements.
        response = HttpResponse()
        response.headers["HX-Trigger"] = "reload-htmx"

        return response


class ArchiveView(MainPageView):
    document_reports = DocumentReport.objects.filter(
        number_of_matches__gte=1).filter(
        resolution_status__isnull=False).order_by("sort_key", "pk")

    def post(self, request, *args, **kwargs):

        is_htmx = self.request.headers.get("HX-Request")
        if is_htmx:
            htmx_trigger = self.request.headers.get("HX-Trigger-Name")
            if htmx_trigger == "revert-match":
                revert_pk = self.request.POST.get("pk")
                dr = DocumentReport.objects.filter(pk=revert_pk)

                res_status = self.request.POST.get('action')
                updates = {
                    'resolution_status': res_status
                }
                if res_status is None:
                    updates['resolution_time'] = None
                dr.update(**updates)

            elif htmx_trigger == "revert-matches":
                dr = DocumentReport.objects.filter(pk__in=self.request.POST.getlist(
                    'table-checkbox'))
                res_status = self.request.POST.get('action')
                updates = {
                    'resolution_status': res_status
                }
                if res_status is None:
                    updates['resolution_time'] = None
                dr.update(**updates)

        # Add a header value to the response before returning to initiate reload of some elements.
        response = HttpResponse()
        response.headers["HX-Trigger"] = "reload-htmx"

        return response

    def dispatch(self, request, *args, **kwargs):
        if settings.ARCHIVE_TAB:
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied(
                _("The archive page has been deactivated for this distribution."))


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
