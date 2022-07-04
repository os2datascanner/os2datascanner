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
# OS2datascanner is developed by Magenta in collaboration with the OS2 public
# sector open source network <https://os2.eu/>.
#
from json import dumps

from django.db import transaction
from django.db.models import F, Q
from django.core.paginator import Paginator, EmptyPage
from django.http import Http404
from pika.exceptions import AMQPError
import structlog

from django.forms import ModelMultipleChoiceField

from os2datascanner.projects.admin.organizations.models import Organization

from .views import RestrictedListView, RestrictedCreateView, \
    RestrictedUpdateView, RestrictedDetailView, RestrictedDeleteView
from ..models.authentication_model import Authentication
from ..models.rules.rule_model import Rule
from ..models.scannerjobs.scanner_model import Scanner, ScanStatus
from ..models.usererrorlog_model import UserErrorLog
from django.utils.translation import ugettext_lazy as _

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = structlog.get_logger(__name__)


class EmptyPagePaginator(Paginator):
    def validate_number(self, number):
        try:
            return super(EmptyPagePaginator, self).validate_number(number)
        except EmptyPage:
            if number > 1:
                return self.num_pages
            else:
                raise Http404(_('The page does not exist'))


class StatusBase(RestrictedListView):

    def get_queryset(self):
        user = self.request.user
        if not user.is_superuser and hasattr(user, 'administrator_for'):
            return self.model.objects.filter(
                scanner__organization__in=[
                    org.uuid for org in
                    user.administrator_for.client.organizations.all()]
            )
        else:
            return super().get_queryset()


# As we do not store the `finished` state of a ScanStatus
# as a field in the DB, we need to infer that state by
# looking at other fields. This is what the ScanStatus.finished
# method does. We can't use that method as a QuerySet filter, though.
# The filter below implements the same behavior without having
# to do two queries, which was previously done (one for getting the
# entire set, then construct a list of pks in Python based on
# ScanStatus.finished, then a second query with a filter based on
# the list).

completed_scans = (
    Q(total_sources__gt=0)
    & Q(total_objects__gt=0)
    & Q(explored_sources=F('total_sources'))
    & Q(scanned_objects__gte=F('total_objects')))


class StatusOverview(StatusBase):
    template_name = "os2datascanner/scan_status.html"
    model = ScanStatus

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

    def get_queryset(self):

        # Only get ScanStatus objects that are not deemed "finished" (see
        # completed_scans Q object above). That way we avoid manual
        # filtering in the template and only get the data we intend to display.

        # Use the same filter as for getting completed scans,
        # but negate it (tilde)

        return super().get_queryset().order_by("-pk").filter(~completed_scans)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["delay"] = "load"
        return context

    def get_template_names(self):
        is_htmx = self.request.headers.get("HX-Request") == 'true'
        return "os2datascanner/scan_status_table.html" if is_htmx \
            else "os2datascanner/scan_status.html"

    def get(self, request, *args, **kwargs):
        if request.headers.get('HX_REQUEST') == "true":
            queryset = self.get_queryset()
            if queryset.exists():
                delay = "every 500ms"
            else:
                delay = "every 10s"
            context = self.get_context_data(object_list=queryset)
            context['delay'] = delay
            context['object_list'] = queryset
            return self.render_to_response(context)
        else:
            return super().get(request, *args, **kwargs)


class StatusCompleted(StatusBase):
    paginate_by = 10
    paginator_class = EmptyPagePaginator
    template_name = "os2datascanner/scan_completed.html"
    model = ScanStatus

    def get_queryset(self):
        """Returns a queryset of Scannerjobs that are finished.

        The queryset consists only of completed scans and is ordered by start time.
        """

        return (
            super().get_queryset()
            .filter(completed_scans)
            .order_by('-scan_tag__time')
        )


class StatusDelete(RestrictedDeleteView):
    model = ScanStatus
    fields = []
    success_url = '/status/'

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()

        return super().get_form(form_class)

    @transaction.atomic
    def form_valid(self):
        # We need to take a lock on the status object here so our background
        # processes can't retrieve it before deletion, update it, and then save
        # it back to the database again
        self.object = self.get_object(
                queryset=self.get_queryset().select_for_update())
        return super().form_valid()


class UserErrorLogView(RestrictedListView):
    """Displays list of errors encountered."""
    template_name = 'os2datascanner/error_log.html'
    model = UserErrorLog

    def get_queryset(self):
        """Order errors by most recent scan."""
        return super().get_queryset().order_by('-scan_status__scan_tag__time')


class ScannerList(RestrictedListView):
    """Displays list of scanners."""

    template_name = 'os2datascanner/scanners.html'
    context_object_name = 'scanner_list'


class ScannerBase(object):
    template_name = 'os2datascanner/scanner_form.html'

    def get_form(self, form_class=None):
        """Get the form for the view.

        Querysets used for choices in the 'domains' and 'rules' fields
        will be limited by the user's organization unless the user is a
        superuser.
        """

        form = super().get_form(form_class)
        user = self.request.user

        form.fields['schedule'].required = False
        form.fields['exclusion_rules'].required = False
        org_qs = Organization.objects.none()
        if hasattr(user, 'administrator_for'):
            org_qs = Organization.objects.filter(
                client=user.administrator_for.client
            )
        elif user.is_superuser:
            org_qs = Organization.objects.all()
        form.fields['organization'].queryset = org_qs

        form.fields["rules"] = ModelMultipleChoiceField(
            Rule.objects.all(),
            validators=ModelMultipleChoiceField.default_validators)

        form.fields["exclusion_rules"] = ModelMultipleChoiceField(
            Rule.objects.all(),
            validators=ModelMultipleChoiceField.default_validators,
            required=False)

        return form

    def get_form_fields(self):
        """Get the list of form fields.

        The 'validation_status' field will be added to the form if the
        user is a superuser.
        """
        fields = super().get_form_fields()
        if self.request.user.is_superuser:
            fields.append('validation_status')

        self.fields = fields
        return fields

    def filter_queryset(self, form, organization):
        for field_name in ['rules', 'exclusion_rules']:
            queryset = form.fields[field_name].queryset
            queryset = queryset.filter(organization=organization)
            form.fields[field_name].queryset = queryset

    def get_scanner_object(self):
        return self.get_object()

    def form_valid(self, form):
        user = self.request.user
        if not user.is_superuser:
            self.object = form.save(commit=False)

        # Makes sure authentication info gets stored in db.
        domain = form.save(commit=False)
        if domain.authentication:
            authentication = domain.authentication
        else:
            authentication = Authentication()

        if 'username' in form.cleaned_data:
            authentication.username = form.cleaned_data['username']
        if 'password' in form.cleaned_data and form.cleaned_data['password'] != "":
            authentication.set_password(str(form.cleaned_data['password']))
        if 'domain' in form.cleaned_data:
            authentication.domain = form.cleaned_data['domain']

        authentication.save()
        domain.authentication = authentication
        domain.save()

        return super().form_valid(form)


class ScannerCreate(ScannerBase, RestrictedCreateView):
    """View for creating a new scannerjob."""


class ScannerUpdate(ScannerBase, RestrictedUpdateView):
    """View for editing an existing scannerjob."""
    edit = True
    old_url = ''
    old_rules = None
    old_user = ''

    def get_form(self, form_class=None):
        """Get the form for the view.

        Querysets used for choices in the 'domains' and 'rules' fields
        will be limited by the user's organization unless the user is a
        superuser.
        """
        form = super().get_form(form_class)
        self.object = self.get_object()
        if hasattr(self.object, "url"):
            self.old_url = self.object.url
        if (hasattr(self.object, "authentication")
                and hasattr(self.object.authentication, "username")):
            self.old_user = self.object.authentication.username
        # Store the existing rules selected in the scannerjob
        self.old_rules = self.object.rules.get_queryset()

        return form

    def get_form_fields(self):
        return super().get_form_fields()

    def form_valid(self, form):
        """Validate the submitted form."""
        if self.old_url != self.object.url:
            self.object.validation_status = Scanner.INVALID

        def is_in_cleaned(entry, comparable):
            data = form.cleaned_data
            return entry in data and data[entry] != comparable

        if is_in_cleaned("url", self.old_url) or is_in_cleaned("username", self.old_user):
            # No password supplied for new username or URL, displaying error to user.
            if 'password' in form.cleaned_data and form.cleaned_data["password"] == "":
                form.add_error("password",
                               _("Password must be updated, when changing username or url."))
                return super().form_invalid(form)
        # Compare the previous set of rules with new selection of rules
        if not set(self.old_rules) == set(form.cleaned_data["rules"]):
            # Reset last scanner-run timestamp if the rule sets differ
            self.object.e2_last_run_at = None
        return super().form_valid(form)


class ScannerDelete(RestrictedDeleteView):
    def get_form(self, form_class=None):
        """Adds special field password and decrypts password."""
        if form_class is None:
            form_class = self.get_form_class()

        return super().get_form(form_class)


class ScannerCopy(ScannerBase, RestrictedCreateView):
    """Creates a copy of an existing scanner. """

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_initial(self):
        initial = super().get_initial()

        scanner_obj = ScannerUpdate.get_scanner_object(self)

        # Copied scannerjobs should be "Invalid" by default
        # to avoid being able to misuse this feature.
        initial["validation_status"] = Scanner.INVALID
        while True:
            scanner_obj.name = f'{scanner_obj.name} Copy'
            if not Scanner.objects.filter(name=scanner_obj.name).exists():
                initial["name"] = scanner_obj.name
                break

        return initial


class ScannerAskRun(RestrictedDetailView):
    """Base class for prompt before starting scan, validate first."""
    fields = []

    def get_context_data(self, **kwargs):
        """Check that user is allowed to run this scanner."""
        context = super().get_context_data(**kwargs)
        last_status = self.object.statuses.last()
        error_message = ""
        if self.object.validation_status is Scanner.INVALID:
            ok = False
            error_message = Scanner.NOT_VALIDATED
        elif not self.object.rules.all():
            ok = False
            error_message = Scanner.HAS_NO_RULES
        elif last_status and not last_status.finished:
            ok = False
            error_message = Scanner.ALREADY_RUNNING
        else:
            ok = True

        context["ok"] = ok

        if not ok:
            context['error_message'] = error_message

        return context


class ScannerRun(RestrictedDetailView):
    """Base class for view that handles starting of a scanner run."""

    fields = []
    template_name = 'os2datascanner/scanner_run.html'
    model = Scanner

    def __init__(self):
        self.object = None

    def get(self, request, *args, **kwargs):
        """Handle a get request to the view."""
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        try:
            context['scan_tag'] = dumps(
                self.object.run(user=request.user), indent=2)
        except Exception as ex:
            logger.error("Error while starting ScannerRun", exc_info=True)
            error_type = type(ex).__name__
            if isinstance(ex, AMQPError):
                context['pika_error'] = f"pika failure [{error_type}]"
            else:
                context['engine2_error'] = f"Engine failure [{error_type}]."
                context['engine2_error'] += ", ".join([str(e) for e in ex.args])

        return self.render_to_response(context)
