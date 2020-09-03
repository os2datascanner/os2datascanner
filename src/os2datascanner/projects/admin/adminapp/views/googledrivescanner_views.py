import json
from django import forms
from django.views.generic.base import TemplateView
from django.views.generic.base import View
from oauth2client.client import OAuth2WebServerFlow
import httplib2
import google_auth_httplib2

from .scanner_views import *
from .views import LoginRequiredMixin
from ..models.scannerjobs.googledrivescanner_model import GoogleDriveScanner
from ... import settings


def make_consent_url():
    if settings.GOOGLEDRIVE_CLIENT_ID is not None:
        build_flow = BuildFlow()
        return build_flow.flow.step1_get_authorize_url()
    else:
        return None


class BuildFlow():
    #TODO
    # Think it should be using site_url from settings, but doesnt work.
    # redirect_uri = settings.SITE_URL + "googledrivescanners/add/"
    flow = OAuth2WebServerFlow(settings.GOOGLEDRIVE_CLIENT_ID,
                               settings.GOOGLEDRIVE_CLIENT_SECRET,
                               scope='https://www.googleapis.com/auth/drive',
                               redirect_uri="http://localhost:8020/googledrivescanners/add/",
                               prompt='consent')


class GoogleDriveScannerList(ScannerList):
    """Displays a list of file scanners."""
    model = GoogleDriveScanner
    type = 'googledrive'


class GoogleDriveScannerCreate(View):
    """Creates a new Google Drive scanner job.
    This view delegates to two other views: one sends the user to Google Drive
    to grant permission for the scan, and the other renders the normal
    scanner job creation form when the response comes back.
    Essentially used as OAuth2CallBack."""

    def dispatch(self, request, *args, **kwargs):
        code = request.GET.get('code', False)
        if not code:
            handler = _GoogleDrivePermissionRequest.as_view()
        else:
            if settings.GOOGLEDRIVE_ACCESS_TOKEN is None:
                oauth_step2 = BuildFlow()
                credentials = oauth_step2.flow.step2_exchange(code)
                credentials_js = json.loads(credentials.to_json())
                settings.GOOGLEDRIVE_ACCESS_TOKEN = credentials_js['access_token']


            handler = _GoogleDriveScannerCreate.as_view()
        return handler(request, *args, **kwargs)


class _GoogleDrivePermissionRequest(TemplateView, LoginRequiredMixin):
    """Sends the user to Google Drive login page"""

    template_name = "os2datascanner/scanner_oauth_start.html"

    def get_context_data(self, **kwargs):
        return dict(**super().get_context_data(**kwargs), **{
            "service_name": "Google Drive",
            "auth_endpoint": make_consent_url(),
            "error": self.request.GET.get("error"),
            "error_description": self.request.GET.get("error_description")
        })


class _GoogleDriveScannerCreate(ScannerCreate):
    """Create a file scanner view"""

    model = GoogleDriveScanner
    fields = [
        'name',
        'schedule',
        'exclusion_rules',
        'access_code',
        'do_ocr',
        'do_last_modified_check',
        'rules',
        'recipients'
    ]

    def get_context_data(self, **kwargs):
        return dict(**super().get_context_data(**kwargs), **{
            "code": self.request.GET['code']
        })

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/googledrivescanners/%s/created/' % self.object.pk


class GoogleDriveScannerUpdate(ScannerUpdate):
    """Update a scanner view."""

    model = GoogleDriveScanner
    fields = [
        'name',
        'schedule',
        'access_code',
        'exclusion_rules',
        'do_ocr',
        'do_last_modified_check',
        'rules',
        'recipients'
    ]

    def get_success_url(self):
        """The URL to redirect to after successful updating.

        Will redirect the user to the validate view if the form was submitted
        with the 'save_and_validate' button.
        """
        if 'save_and_validate' in self.request.POST:
            return 'validate/'
        else:
            return '/googledrivescanners/%s/saved/' % self.object.pk


class GoogleDriveScannerDelete(ScannerDelete):
    """Delete a scanner view."""
    model = GoogleDriveScanner
    fields = []
    success_url = '/googledrivescanners/'


class GoogleDriveScannerAskRun(ScannerAskRun):
    """Prompt for starting google drive scan, validate first."""
    model = GoogleDriveScanner


class GoogleDriveScannerRun(ScannerRun):
    """View that handles starting of a scanner run."""
    model = GoogleDriveScanner
