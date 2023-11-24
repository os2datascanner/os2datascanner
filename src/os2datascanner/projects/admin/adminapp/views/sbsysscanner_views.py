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
from django.conf import settings
from django.views import View
from django.views.generic.base import TemplateView

from .views import LoginRequiredMixin
from .scanner_views import (ScannerRun, ScannerList,
                            ScannerAskRun, ScannerCreate, ScannerDelete, ScannerUpdate)
from ..models.scannerjobs.sbsysscanner import SbsysScanner


class SbsysScannerList(ScannerList):
    model = SbsysScanner
    type = 'sbsys'


class SbsysScannerCreate(View):
    """Delegates to two views. One to the regular scannerjob creation
    and one that states Sbsys has not been configured,
    which means no token_url or no client_id or client_secret"""

    def dispatch(self, request, *args, **kwargs):
        if settings.SBSYS_TOKEN_URL and settings.SBSYS_CLIENT_ID \
                and settings.SBSYS_CLIENT_SECRET and settings.SBSYS_API_URL:
            handler = _SbsysScannerCreate.as_view()
        else:
            handler = _SbsysNoPermission.as_view()
        return handler(request, *args, **kwargs)


class _SbsysNoPermission(LoginRequiredMixin, TemplateView):
    # TODO make a more fitting template or adjust that one
    template_name = "components/scanner/scanner_no_client_credentials.html"


class _SbsysScannerCreate(ScannerCreate):
    """Creates a Sbsys scannerjob"""
    model = SbsysScanner
    type = "sbsys"
    fields = ['name', 'schedule', 'do_ocr', 'only_notify_superadmin',
              'do_last_modified_check', 'rules', 'organization',
              'keep_false_positives']

    def get_success_url(self):
        return '/sbsysscanners/%s/saved/' % self.object.pk


class SbsysScannerUpdate(ScannerUpdate):
    """Displays parameters of existing Sbsys scannerjob for modification"""
    model = SbsysScanner
    type = "sbsys"
    fields = ['name', 'schedule', 'do_ocr', 'only_notify_superadmin',
              'do_last_modified_check', 'rules', 'organization',
              'keep_false_positives']

    def get_success_url(self):
        return '/sbsysscanners/%s/saved/' % self.object.pk


class SbsysScannerDelete(ScannerDelete):
    """ Deletes a Sbsys scannerjob"""
    model = SbsysScanner
    type = "sbsys"
    fields = []
    success_url = '/sbsysscanners/'


class SbsysScannerAskRun(ScannerAskRun):
    """Prompts for confirmation before running scannerjob"""
    model = SbsysScanner


class SbsysScannerRun(ScannerRun):
    """ Runs the Sbsys scannerjob."""
    model = SbsysScanner
