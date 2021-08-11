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

from django.core.paginator import Paginator, EmptyPage
from django.http import Http404
from pika.exceptions import AMQPError
import structlog

from django.forms import ModelMultipleChoiceField
from django.forms.models import modelform_factory
from django.conf import settings

from os2datascanner.projects.admin.organizations.models import Organization

from .views import RestrictedListView, RestrictedCreateView, \
    RestrictedUpdateView, RestrictedDetailView, RestrictedDeleteView
from ..models.authentication_model import Authentication
from ..models.rules.rule_model import Rule
from ..models.scannerjobs.scanner_model import Scanner, ScanStatus
from django.utils.translation import ugettext_lazy as _

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
                scanner__organization__in=
                [org.uuid for org in
                 user.administrator_for.client.organizations.all()]
            )
        else:
            return super().get_queryset()


class StatusOverview(StatusBase):
    template_name = "os2datascanner/scan_status.html"
    model = ScanStatus

    def get_queryset(self):
        return super().get_queryset().order_by("-pk")


class StatusCompleted(StatusBase):
    paginate_by = 10
    paginator_class = EmptyPagePaginator
    template_name = "os2datascanner/scan_completed.html"
    model = ScanStatus

    def get_queryset(self):
        """ Returns a queryset of Scannerjobs that are finished"""

        # When a scannerjob is run, we immediately create a ScanStatus object,
        # but we use a property to get whether or not it is finished.
        # This means we have to do filtering some filtering in Python and
        # then reconstruct a queryset, to not include not-finished scannerjobs.
        finished_scannerjobs = set()

        for scannerjob in super().get_queryset().order_by("-pk"):
            if scannerjob.finished:
                finished_scannerjobs.add(scannerjob.pk)

        return super().get_queryset().filter(pk__in=finished_scannerjobs)


class StatusDelete(RestrictedDeleteView):
    model = ScanStatus
    fields = []
    success_url = '/status/'

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()

        return super().get_form(form_class)


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
        for field_name in ['rules']:
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
        if 'password' in form.cleaned_data:
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

    def get_form(self, form_class=None):
        """Get the form for the view.

        Querysets used for choices in the 'domains' and 'rules' fields
        will be limited by the user's organization unless the user is a
        superuser.
        """
        form = super().get_form(form_class)
        self.old_url = self.get_object().url
        # Store the existing rules selected in the scannerjob
        self.old_rules = self.object.rules.get_queryset()

        return form

    def form_valid(self, form):
        """Validate the submitted form."""
        if self.old_url != self.object.url:
            self.object.validation_status = Scanner.INVALID
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

        if not ok:
            context['error_message'] = error_message
        if settings.DEBUG:
            # run the scanner job if we're in debug mode
            ok = True
        context['ok'] = ok

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
