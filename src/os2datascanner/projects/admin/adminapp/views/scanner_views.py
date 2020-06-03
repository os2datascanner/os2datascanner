from json import dumps
from pika.exceptions import AMQPError

from django.db.models import Q
from django.forms import ModelMultipleChoiceField

from .views import RestrictedListView, RestrictedCreateView, \
    RestrictedUpdateView, RestrictedDetailView, RestrictedDeleteView
from ..models.authentication_model import Authentication
from ..models.rules.rule_model import Rule
from ..models.scannerjobs.scanner_model import Scanner
from ..models.userprofile_model import UserProfile

from os2datascanner.engine2.model.core import ResourceUnavailableError


class ScannerList(RestrictedListView):
    """Displays list of scanners."""

    template_name = 'os2datascanner/scanners.html'
    context_object_name = 'scanner_list'

    def get_queryset(self):
        """Get queryset, don't include non-visible scanners."""
        qs = super().get_queryset()
        # Dismiss scans that are not visible
        qs = qs.filter(is_visible=True)
        return qs


class ScannerBase():
    template_name = 'os2datascanner/scanner_form.html'

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

    def get_form(self, form_class=None):

        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)
        form.fields['schedule'].required = False

        # Exclude recipients with no email address
        form.fields[
            'recipients'
        ].queryset = form.fields[
            'recipients'
        ].queryset.exclude(user__email="")

        return form

    def get_scanner_object(self):
        return self.get_object()

    def form_valid(self, form):
        if not self.request.user.is_superuser:
            user_profile = self.request.user.profile
            self.object = form.save(commit=False)
            self.object.organization = user_profile.organization

        """Makes sure authentication info gets stored in db."""
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

    def get_form(self, form_class=None):
        """Get the form for the view.

        Querysets used for choices in the 'domains' and 'rules' fields
        will be limited by the user's organization unless the user is a
        superuser.
        """
        form = super().get_form(form_class)
        try:
            organization = self.request.user.profile.organization
            groups = self.request.user.profile.groups.all()
        except UserProfile.DoesNotExist:
            organization = None
            groups = None

        if not self.request.user.is_superuser:
            self.filter_queryset(form, groups, organization)

        form.fields["rules"] = ModelMultipleChoiceField(
                Rule.objects.all(),
                validators=ModelMultipleChoiceField.default_validators)

        return form

    def filter_queryset(self, form, groups, organization):
        for field_name in ['rules', 'recipients']:
            queryset = form.fields[field_name].queryset
            queryset = queryset.filter(organization=organization)
            if (self.request.user.profile.is_group_admin or
                            field_name == 'recipients'):
                # Already filtered by organization, nothing more to do.
                pass
            else:
                queryset = queryset.filter(
                    Q(group__in=groups) | Q(group__isnull=True)
                )
            form.fields[field_name].queryset = queryset


class ScannerUpdate(ScannerBase, RestrictedUpdateView):
    """View for editing an existing scannerjob."""
    edit = True
    old_url = ''

    def get_form(self, form_class=None):
        """Get the form for the view.

        Querysets used for choices in the 'domains' and 'rules' fields
        will be limited by the user's organization unless the user is a
        superuser.
        """
        self.old_url = self.get_object().url
        form = super().get_form(form_class)
        self.filter_queryset(form, self.get_scanner_object())
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

    def filter_queryset(self, form, scanner):
        for field_name in ['rules', 'recipients']:
            queryset = form.fields[field_name].queryset
            queryset = queryset.filter(organization=scanner.organization)

            if scanner.organization.do_use_groups:
                # TODO: This is not very elegant!
                if field_name == 'recipients':
                    if scanner.group:
                        queryset = queryset.filter(
                            Q(groups__in=scanner.group) |
                            Q(groups__isnull=True)
                        )
                else:
                    queryset = queryset.filter(
                        Q(group=scanner.group) | Q(group__isnull=True)
                    )
            form.fields[field_name].queryset = queryset

    def form_valid(self, form):
        """Validate the submitted form."""
        if self.old_url != self.object.url:
            self.object.validation_status = Scanner.INVALID

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

        if not self.object.rules.all():
            ok = False
            error_message = Scanner.HAS_NO_RULES
        else:
            ok = True

        context['ok'] = ok
        if not ok:
            context['error_message'] = error_message

        return context


class ScannerRun(RestrictedDetailView):

    """Base class for view that handles starting of a scanner run."""

    template_name = 'os2datascanner/scanner_run.html'
    model = Scanner

    def __init__(self):
        self.object = None

    def get(self, request, *args, **kwargs):
        """Handle a get request to the view."""
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        try:
            context['scan_tag'] = dumps(self.object.run(user=request.user))
        except ResourceUnavailableError as ex:
            source = ex.args[0]
            details = ex.args[1:]
            context['engine2_error'] = ", ".join([str(d) for d in details])
        except AMQPError as ex:
            context['pika_error'] = type(ex).__name__

        return self.render_to_response(context)
