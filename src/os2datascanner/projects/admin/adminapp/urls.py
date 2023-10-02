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
"""URL mappings."""

import django.contrib.auth.views
from django.urls import re_path
from django.http import HttpResponse
from django.views.i18n import JavaScriptCatalog
from django.views.generic.base import TemplateView
from os2datascanner import __version__, __commit__, __tag__, __branch__
from os2datascanner.projects.admin.adminapp.views.analysis_views import AnalysisPageView

from os2datascanner.projects.admin import settings

from .models.scannerjobs.dropboxscanner import DropboxScanner
from .models.scannerjobs.exchangescanner import ExchangeScanner
from .models.scannerjobs.filescanner import FileScanner
from .models.scannerjobs.webscanner import WebScanner
from .models.scannerjobs.googledrivescanner import GoogleDriveScanner
from .models.scannerjobs.msgraph import (MSGraphMailScanner,
                                         MSGraphFileScanner,
                                         MSGraphCalendarScanner,
                                         MSGraphTeamsFileScanner)
from .models.scannerjobs.gmail import GmailScanner
from .models.scannerjobs.sbsysscanner import SbsysScanner
from .views.api import JSONAPIView
from .views.views import GuideView, DialogSuccess

from .views.exchangescanner_views import (ExchangeScannerList, ExchangeScannerCreate,
                                          ExchangeScannerUpdate, ExchangeScannerDelete,
                                          ExchangeScannerRun, ExchangeScannerAskRun,
                                          ExchangeScannerCopy, ExchangeCleanupStaleAccounts,
                                          OrganizationalUnitListing)

from .views.filescanner_views import (FileScannerCreate, FileScannerRun,
                                      FileScannerAskRun, FileScannerUpdate,
                                      FileScannerDelete, FileScannerList,
                                      FileScannerCopy)

from .views.dropboxscanner_views import (DropboxScannerCreate, DropboxScannerRun,
                                         DropboxScannerAskRun, DropboxScannerUpdate,
                                         DropboxScannerDelete, DropboxScannerList)

from .views.googledrivescanner_views import (GoogleDriveScannerCreate, GoogleDriveScannerRun,
                                             GoogleDriveScannerAskRun, GoogleDriveScannerUpdate,
                                             GoogleDriveScannerList, GoogleDriveScannerDelete,
                                             GoogleDriveScannerCopy)

from .views.gmailscanner_views import (GmailScannerCreate, GmailScannerRun,
                                       GmailScannerAskRun, GmailScannerUpdate,
                                       GmailScannerDelete, GmailScannerList,
                                       GmailScannerCopy)

from .views.sbsysscanner_views import (SbsysScannerCreate, SbsysScannerList,
                                       SbsysScannerAskRun, SbsysScannerDelete,
                                       SbsysScannerRun, SbsysScannerUpdate)

from .views.rule_views import (RuleList, CPRRuleCreate,
                               CPRRuleUpdate, CPRRuleDelete,
                               RegexRuleCreate, RegexRuleUpdate,
                               RegexRuleDelete, CustomRuleCreate,
                               CustomRuleUpdate, CustomRuleDelete)

from .views.scanner_views import (StatusOverview, StatusCompleted,
                                  StatusDelete, StatusTimeline, UserErrorLogView,
                                  UserErrorLogCSVView)

from .views.webscanner_views import (WebScannerCreate, WebScannerUpdate,
                                     WebScannerDelete, WebScannerRun,
                                     WebScannerAskRun, WebScannerList,
                                     WebScannerValidate, WebScannerCopy)

from .views.msgraph_views import (MSGraphMailList, MSGraphMailDelete,
                                  MSGraphMailCreate, MSGraphMailUpdate,
                                  MSGraphMailRun, MSGraphMailAskRun,
                                  MSGraphFileList, MSGraphFileDelete,
                                  MSGraphFileCreate, MSGraphFileUpdate,
                                  MSGraphFileRun, MSGraphFileAskRun,
                                  MSGraphMailCopy, MSGraphFileCopy,
                                  MSGraphCalendarList, MSGraphCalendarDelete,
                                  MSGraphCalendarCreate, MSGraphCalendarUpdate,
                                  MSGraphCalendarRun, MSGraphCalendarAskRun,
                                  MSGraphCalendarCopy, MSGraphTeamsFileList,
                                  MSGraphTeamsFileDelete, MSGraphTeamsFileCreate,
                                  MSGraphTeamsFileUpdate, MSGraphTeamsFileRun,
                                  MSGraphTeamsFileAskRun, MSGraphTeamsFileCopy,
                                  MSGraphCalendarCleanupStaleAccounts,
                                  MSGraphFileCleanupStaleAccounts,
                                  MSGraphMailCleanupStaleAccounts)

from .views.miniscanner_views import MiniScanner, execute_mini_scan

urlpatterns = [
    # App URLs
    re_path(r'^$', WebScannerList.as_view(), name='index'),
    re_path(r'^api/openapi.yaml$', TemplateView.as_view(
        template_name="openapi.yaml", content_type="application/yaml"),
        name="json-api"),
    re_path(r'^api/(?P<path>.*)$', JSONAPIView.as_view(), name="json-api"),
    re_path(r'^analysis/$',  AnalysisPageView.as_view(), name='analysis'),

    # App URLs
    re_path(r'^status/$', StatusOverview.as_view(), name='status'),
    re_path(r'^status-completed/$', StatusCompleted.as_view(), name='status-completed'),
    re_path(r'^status-completed/timeline/(?P<pk>\d+)/$',
            StatusTimeline.as_view(), name='status-timeline'),
    re_path(r'^error-log/$', UserErrorLogView.as_view(), name='error-log'),
    re_path(r'^error-log/csv/$', UserErrorLogCSVView.as_view(), name='export-error-log'),
    re_path(r'^status/(?P<pk>\d+)/delete/$', StatusDelete.as_view(), name='status-delete'),
    re_path(r'^help/guide/$', GuideView.as_view(), name='guide'),
    # Exchangescanner RE_PATH's
    re_path(r'^org-units-listing/', OrganizationalUnitListing.as_view(), name='org-units-listing'),
    re_path(r'^exchangescanners/$', ExchangeScannerList.as_view(), name='exchangescanners'),
    re_path(r'^exchangescanners/add/$',
            ExchangeScannerCreate.as_view(),
            name='exchangescanner_add'),
    re_path(r'^exchangescanners/(?P<pk>\d+)/delete/$', ExchangeScannerDelete.as_view(),
            name='exchangescanner_delete'),
    re_path(r'^exchangescanners/(?P<pk>\d+)/$', ExchangeScannerUpdate.as_view(),
            name='exchangescanner_update'),
    re_path(r'^exchangescanners/(?P<pk>\d+)/run/$', ExchangeScannerRun.as_view(),
            name='exchangescanner_run'),
    re_path(r'^exchangescanners/(?P<pk>\d+)/askrun/$',
            ExchangeScannerAskRun.as_view(
                template_name='os2datascanner/scanner_askrun.html',
                model=ExchangeScanner),
            name='scanner_askrun'),
    re_path(r'^exchangescanners/(?P<pk>\d+)/copy/$', ExchangeScannerCopy.as_view(),
            name='exchangescanner_copy'),
    re_path(r'^exchangescanners/(?P<pk>\d+)/cleanup_stale_accounts/$',
            ExchangeCleanupStaleAccounts.as_view(), name='exchangescanner_cleanup'),

    # Webscanner URLs
    re_path(r'^webscanners/$', WebScannerList.as_view(), name='webscanners'),
    re_path(r'^webscanners/add/$', WebScannerCreate.as_view(), name='webscanner_add'),
    re_path(r'^webscanners/(?P<pk>\d+)/delete/$', WebScannerDelete.as_view(),
            name='webscanner_delete'),
    re_path(r'^webscanners/(?P<pk>\d+)/validate/$', WebScannerValidate.as_view(),
            name='web_scanner_validate'),
    re_path(r'^webscanners/(?P<pk>\d+)/run/$', WebScannerRun.as_view(),
            name='webscanner_run'),
    re_path(r'^webscanners/(?P<pk>\d+)/askrun/$',
            WebScannerAskRun.as_view(
                template_name='os2datascanner/scanner_askrun.html',
                model=WebScanner),
            name='webscanner_askrun'),
    re_path(r'^webscanners/(?P<pk>\d+)/$', WebScannerUpdate.as_view(),
            name='webscanner_update'),
    re_path(r'^webscanners/(?P<pk>\d+)/copy/$', WebScannerCopy.as_view(), name='webscanner_copy'),

    # Filescanner URLs
    re_path(r'^filescanners/$', FileScannerList.as_view(), name='filescanners'),
    re_path(r'^filescanners/add/$', FileScannerCreate.as_view(), name='filescanner_add'),
    re_path(r'^filescanners/(?P<pk>\d+)/$', FileScannerUpdate.as_view(),
            name='filescanner_update'),
    re_path(r'^filescanners/(?P<pk>\d+)/delete/$', FileScannerDelete.as_view(),
            name='filescanner_delete'),
    re_path(r'^filescanners/(?P<pk>\d+)/run/$', FileScannerRun.as_view(),
            name='filescanner_run'),
    re_path(r'^filescanners/(?P<pk>\d+)/askrun/$',
            FileScannerAskRun.as_view(
                template_name='os2datascanner/scanner_askrun.html',
                model=FileScanner),
            name='filescanner_askrun'),
    re_path(r'^filescanners/(?P<pk>\d+)/copy/$',
            FileScannerCopy.as_view(),
            name='filescanner_copy'),

    # Dropbox scanner URLs
    re_path(r'^dropboxscanners/$', DropboxScannerList.as_view(), name='dropboxscanners'),
    re_path(r'^dropboxscanners/add/$', DropboxScannerCreate.as_view(), name='dropboxscanner_add'),
    re_path(r'^dropboxscanners/(?P<pk>\d+)/$', DropboxScannerUpdate.as_view(),
            name='dropboxscanner_update'),
    re_path(r'^dropboxscanners/(?P<pk>\d+)/delete/$', DropboxScannerDelete.as_view(),
            name='dropboxscanner_delete'),
    re_path(r'^dropboxscanners/(?P<pk>\d+)/run/$', DropboxScannerRun.as_view(),
            name='dropboxscanner_run'),
    re_path(r'^dropboxscanners/(?P<pk>\d+)/askrun/$',
            DropboxScannerAskRun.as_view(
                template_name='os2datascanner/scanner_askrun.html',
                model=DropboxScanner),
            name='dropboxscanner_askrun'),

    # Google Drive scanner URLs
    re_path(r'^googledrivescanners/$', GoogleDriveScannerList.as_view(),
            name='googledrivescanners'),
    re_path(r'^googledrivescanners/add/$', GoogleDriveScannerCreate.as_view(),
            name='googledrivescanner_add'),
    re_path(r'^googledrivescanners/(?P<pk>\d+)/$', GoogleDriveScannerUpdate.as_view(),
            name='googledrivescanner_update'),
    re_path(r'^googledrivescanners/(?P<pk>\d+)/delete/$', GoogleDriveScannerDelete.as_view(),
            name='googledrivescanner_delete'),
    re_path(r'^googledrivescanners/(?P<pk>\d+)/run/$', GoogleDriveScannerRun.as_view(),
            name='googledrivescanner_run'),
    re_path(r'^googledrivescanners/(?P<pk>\d+)/askrun/$',
            GoogleDriveScannerAskRun.as_view(
                template_name='os2datascanner/scanner_askrun.html',
                model=GoogleDriveScanner),
            name='googledrivescanner_askrun'),
    re_path(r'^googledrivescanners/(?P<pk>\d+)/copy/$', GoogleDriveScannerCopy.as_view(),
            name='googledrivescanner_copy'),

    # Gmail scanner URLs
    re_path(r'^gmailscanners/$', GmailScannerList.as_view(), name='gmailscanners'),
    re_path(r'^gmailscanners/add/$', GmailScannerCreate.as_view(), name='gmailscanner_add'),
    re_path(r'^gmailscanners/(?P<pk>\d+)/$', GmailScannerUpdate.as_view(),
            name='gmailscanner_update'),
    re_path(r'^gmailscanners/(?P<pk>\d+)/delete/$', GmailScannerDelete.as_view(),
            name='gmailscanner_delete'),
    re_path(r'^gmailscanners/(?P<pk>\d+)/run/$', GmailScannerRun.as_view(),
            name='gmailscanner_run'),
    re_path(r'^gmailscanners/(?P<pk>\d+)/askrun/$',
            GmailScannerAskRun.as_view(
                template_name='os2datascanner/scanner_askrun.html',
                model=GmailScanner),
            name='gmailscanner_askrun'),
    re_path(r'^gmailscanners/(?P<pk>\d+)/copy/$',
            GmailScannerCopy.as_view(),
            name='gmailscanner_copy'),

    # Sbsys scanner URLs
    re_path(r'^sbsysscanners/$', SbsysScannerList.as_view(), name='sbsysscanners'),
    re_path(r'^sbsysscanners/add/$', SbsysScannerCreate.as_view(), name='sbsysscanner_add'),
    re_path(r'^sbsysscanners/(?P<pk>\d+)/$', SbsysScannerUpdate.as_view(),
            name='sbsysscanner_update'),
    re_path(r'^sbsysscanners/(?P<pk>\d+)/delete/$', SbsysScannerDelete.as_view(),
            name='sbsysscanner_delete'),
    re_path(r'^sbsysscanners/(?P<pk>\d+)/run/$', SbsysScannerRun.as_view(),
            name='sbsysscanner_run'),
    re_path(r'^sbsysscanners/(?P<pk>\d+)/askrun/$',
            SbsysScannerAskRun.as_view(
                template_name='os2datascanner/scanner_askrun.html',
                model=SbsysScanner),
            name='sbsysscanner_askrun'),

    # OAuth-based data sources
    re_path(r'^msgraph-calendarscanners/$',
            MSGraphCalendarList.as_view(),
            name='msgraphcalendarscanner_list'),
    re_path(r'^msgraph-calendarscanners/add/$',
            MSGraphCalendarCreate.as_view(),
            name='msgraphcalendarscanner_add'),
    re_path(r'^msgraph-calendarscanners/(?P<pk>\d+)/$',
            MSGraphCalendarUpdate.as_view(),
            name='msgraphcalendarscanner_update'),
    re_path(r'^msgraph-calendarscanners/(?P<pk>\d+)/delete/$',
            MSGraphCalendarDelete.as_view(),
            name='msgraphcalendarscanner_delete'),
    re_path(r'^msgraph-calendarscanners/(?P<pk>\d+)/copy/$',
            MSGraphCalendarCopy.as_view(),
            name='msgraphcalendarscanner_copy'),
    re_path(r'^msgraph-calendarscanners/(?P<pk>\d+)/run/$',
            MSGraphCalendarRun.as_view(),
            name='msgraphcalendarscanner_run'),
    re_path(r'^msgraph-calendarscanners/(?P<pk>\d+)/askrun/$',
            MSGraphCalendarAskRun.as_view(
                template_name='os2datascanner/scanner_askrun.html',
                model=MSGraphCalendarScanner),
            name='msgraphcalendarscanner_askrun'),
    re_path(r'^(msgraph-calendarscanners)/(\d+)/(created|saved)/$',
            DialogSuccess.as_view()),
    re_path(r'^msgraph-calendarscanners/(?P<pk>\d+)/cleanup_stale_accounts/$',
            MSGraphCalendarCleanupStaleAccounts.as_view(), name='msgraphcalendarscanner_cleanup'),
    re_path(r'^msgraph-filescanners/$',
            MSGraphFileList.as_view(),
            name='msgraphfilescanner_list'),
    re_path(r'^msgraph-filescanners/add/$',
            MSGraphFileCreate.as_view(),
            name='msgraphfilescanner_add'),
    re_path(r'^msgraph-filescanners/(?P<pk>\d+)/$',
            MSGraphFileUpdate.as_view(),
            name='msgraphfilescanner_update'),
    re_path(r'^msgraph-mailscanners/(?P<pk>\d+)/$',
            MSGraphMailUpdate.as_view(),
            name='msgraphmailscanner_update'),
    re_path(r'^msgraph-filescanners/(?P<pk>\d+)/cleanup_stale_accounts/$',
            MSGraphFileCleanupStaleAccounts.as_view(), name='msgraphfilescanner_cleanup'),
    re_path(r'^msgraph-mailscanners/(?P<pk>\d+)/cleanup_stale_accounts/$',
            MSGraphMailCleanupStaleAccounts.as_view(), name='msgraphmailscanner_cleanup'),
    re_path(r'^msgraph-filescanners/(?P<pk>\d+)/delete/$',
            MSGraphFileDelete.as_view(),
            name='msgraphfilescanner_delete'),
    re_path(r'^msgraph-filescanners/(?P<pk>\d+)/copy/$', MSGraphFileCopy.as_view(),
            name='filescanners_copy'),
    re_path(r'^msgraph-filescanners/(?P<pk>\d+)/run/$',
            MSGraphFileRun.as_view(),
            name='msgraphfilescanner_run'),
    re_path(r'^msgraph-filescanners/(?P<pk>\d+)/askrun/$',
            MSGraphFileAskRun.as_view(
                template_name='os2datascanner/scanner_askrun.html',
                model=MSGraphFileScanner),
            name='msgraphfilescanner_askrun'),

    re_path(r'^msgraph-mailscanners/$',
            MSGraphMailList.as_view(),
            name='msgraphmailscanner_list'),
    re_path(r'^msgraph-mailscanners/add/$',
            MSGraphMailCreate.as_view(),
            name='msgraphmailscanner_add'),
    re_path(r'^msgraph-mailscanners/(?P<pk>\d+)/$',
            MSGraphMailUpdate.as_view(),
            name='msgraphmailscanner_update'),
    re_path(r'^msgraph-mailscanners/(?P<pk>\d+)/delete/$',
            MSGraphMailDelete.as_view(),
            name='msgraphmailscanner_delete'),
    re_path(r'^msgraph-mailscanners/(?P<pk>\d+)/copy/$', MSGraphMailCopy.as_view(),
            name='msgraphmailscanner_copy'),
    re_path(r'^msgraph-mailscanners/(?P<pk>\d+)/run/$',
            MSGraphMailRun.as_view(),
            name='msgraphmailscanner_run'),
    re_path(r'^msgraph-mailscanners/(?P<pk>\d+)/askrun/$',
            MSGraphMailAskRun.as_view(
                template_name='os2datascanner/scanner_askrun.html',
                model=MSGraphMailScanner),
            name='msgraphmailscanner_askrun'),
    re_path(r'^(msgraph-mailscanners|msgraph-filescanners)/(\d+)/(created|saved)/$',
            DialogSuccess.as_view()),

    re_path(r'^msgraph-teams-filescanners/$',
            MSGraphTeamsFileList.as_view(),
            name='msgraphteamsfilescanner_list'),
    re_path(r'^msgraph-teams-filescanners/add/$',
            MSGraphTeamsFileCreate.as_view(),
            name='msgraphteamsfilescanner_add'),
    re_path(r'^msgraph-teams-filescanners/(?P<pk>\d+)/$',
            MSGraphTeamsFileUpdate.as_view(),
            name='msgraphteamsfilescanner_update'),
    re_path(r'^msgraph-teams-filescanners/(?P<pk>\d+)/delete/$',
            MSGraphTeamsFileDelete.as_view(),
            name='msgraphteamsfilescanner_delete'),
    re_path(r'^msgraph-teams-filescanners/(?P<pk>\d+)/copy/$', MSGraphTeamsFileCopy.as_view(),
            name='msgraphfilescanners_copy'),
    re_path(r'^msgraph-teams-filescanners/(?P<pk>\d+)/run/$',
            MSGraphTeamsFileRun.as_view(),
            name='msgraphteamsfilescanner_run'),
    re_path(r'^msgraph-teams-filescanners/(?P<pk>\d+)/askrun/$',
            MSGraphTeamsFileAskRun.as_view(
                template_name='os2datascanner/scanner_askrun.html',
                model=MSGraphTeamsFileScanner),
            name='msgraphteamsfilescanner_askrun'),
    re_path(r'^(msgraph-teams-filescanners|msgraph-filescanners)/(\d+)/(created|saved)/$',
            DialogSuccess.as_view()),

    # Rules
    re_path(r'^rules/$', RuleList.as_view(), name='rules'),
    re_path(r'^rules/cpr/add/$', CPRRuleCreate.as_view(), name='cprrule_add'),
    re_path(r'^rules/cpr/(?P<pk>\d+)/$', CPRRuleUpdate.as_view(),
            name='cprrule_update'),
    re_path(r'^rules/cpr/(?P<pk>\d+)/delete/$', CPRRuleDelete.as_view(),
            name='cprrule_delete'),
    re_path(r'^rules/regex/add/$', RegexRuleCreate.as_view(), name='regexrule_add'),
    re_path(r'^rules/regex/(?P<pk>\d+)/$', RegexRuleUpdate.as_view(),
            name='rule_update'),
    re_path(r'^rules/regex/(?P<pk>\d+)/delete/$', RegexRuleDelete.as_view(),
            name='rule_delete'),
    re_path(r'^rules/custom/add/$', CustomRuleCreate.as_view(), name='customrule_add'),
    re_path(r'^rules/custom/(?P<pk>\d+)/$', CustomRuleUpdate.as_view(),
            name='customrule_update'),
    re_path(r'^rules/custom/(?P<pk>\d+)/delete/$', CustomRuleDelete.as_view(),
            name='customrule_delete'),
    # Login/logout stuff
    re_path(r'^accounts/login/',
            django.contrib.auth.views.LoginView.as_view(
                template_name='login.html',
            ),
            name='login'),
    re_path(r'^accounts/logout/',
            django.contrib.auth.views.LogoutView.as_view(
                template_name='logout.html',
            ),
            name='logout'),
    re_path(r'^accounts/password_change/',
            django.contrib.auth.views.PasswordChangeView.as_view(
                template_name='password_change.html',
            ),
            name='password_change'),
    re_path(r'^accounts/password_change_done/',
            django.contrib.auth.views.PasswordChangeDoneView.as_view(
                template_name='password_change_done.html',
            ),
            name='password_change_done'),
    re_path(r'^accounts/password_reset/$',
            django.contrib.auth.views.PasswordResetView.as_view(
                template_name='password_reset_form.html',
            ),
            name='password_reset'),
    re_path(r'^accounts/password_reset/done/',
            django.contrib.auth.views.PasswordResetDoneView.as_view(
                template_name='password_reset_done.html',
            ),
            name='password_reset_done'),
    re_path(r'^accounts/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/' +
            '(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]*)/',
            django.contrib.auth.views.PasswordResetConfirmView.as_view(
                template_name='password_reset_confirm.html',
            ),
            name='password_reset_confirm'),
    re_path(r'^accounts/reset/complete',
            django.contrib.auth.views.PasswordResetCompleteView.as_view(
                template_name='password_reset_complete.html',
            ),
            name='password_reset_complete'),

    # General success handler
    re_path(r'^(webscanners|filescanners|exchangescanners|dropboxscanners|googledrivescanners|gmailscanners|sbsysscanners)/(\d+)/(created)/$',  # noqa
            DialogSuccess.as_view()),
    re_path(r'^(webscanners|filescanners|exchangescanners|dropboxscanners|googledrivescanners|gmailscanners|sbsysscanners)/(\d+)/(saved)/$',  # noqa
            DialogSuccess.as_view()),
    re_path(r'^(rules/regex|rules/cpr)/(\d+)/(created)/$',
            DialogSuccess.as_view()),
    re_path(r'^(rules/regex|rules/cpr)/(\d+)/(saved)/$',
            DialogSuccess.as_view()),

    re_path(r'^jsi18n/$',
            JavaScriptCatalog.as_view(
                packages=('os2datascanner.projects.admin.adminapp', 'recurrence')),
            name="jsi18n"),

    re_path(r'^health/', lambda r: HttpResponse()),
    re_path(r'^version/?$', lambda r: HttpResponse(
        f"""
        Version:   {__version__}<br/>
        Commit-ID: {__commit__}<br/>
        Tag:       {__tag__}<br/>
        Branch:    {__branch__}
        """)),
]

if settings.ENABLE_MINISCAN:
    urlpatterns.extend([
        re_path(r"^miniscan/$", MiniScanner.as_view(), name="miniscan"),
        re_path(r"^miniscan/run/$", execute_mini_scan, name="miniscan_run"),
    ])
