from json import dumps
from django.conf import settings
from django.views import View
from django.views.generic.base import TemplateView
from urllib.parse import urlencode

from ..models.scannerjobs.msgraph_models import MSGraphMailScanner
from .views import LoginRequiredMixin
from .scanner_views import ScannerCreate


auth_endpoint = "https://login.microsoftonline.com/common/adminconsent?client_id={client_id}&scope=https://graph.microsoft.com/.default&response_type=code"


class MSGraphMailCreate(View):
    def dispatch(self, request, *args, **kwargs):
        if 'tenant' in request.GET:
            handler = _MSGraphMailCreate.as_view()
        else:
            handler = _MSGraphMailPermissionRequest.as_view()
        return handler(request, *args, **kwargs)


class _MSGraphMailPermissionRequest(TemplateView, LoginRequiredMixin):
    template_name = "os2datascanner/scanner_oauth_start.html"

    @staticmethod
    def make_endpoint_url():
        if settings.MSGRAPH_APP_ID is not None:
            return auth_endpoint.format(client_id=settings.MSGRAPH_APP_ID)
        else:
            return None

    def get_context_data(self, **kwargs):
        return dict(**super().get_context_data(**kwargs), **{
            "service_name": "Microsoft Online",
            "auth_endpoint": _MSGraphMailPermissionRequest.make_endpoint_url(),
        })


class _MSGraphMailCreate(ScannerCreate):
    model = MSGraphMailScanner
    type = 'msgraph-mail'
    fields = ['name', 'schedule', 'tenant_id', 'do_ocr',
              'do_last_modified_check', 'rules', 'recipients']

    def get_context_data(self, **kwargs):
        return dict(**super().get_context_data(**kwargs), **{
            "tenant_id": self.request.GET['tenant']
        })
