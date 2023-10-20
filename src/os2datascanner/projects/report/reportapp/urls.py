import django_saml2_auth.views
import django.contrib.auth.views
from django.urls import re_path
from django.http import HttpResponse
from django.urls import include
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path
from django.views.i18n import JavaScriptCatalog
from os2datascanner import __version__

from .views.api import JSONAPIView
from .views.saml import metadata
from .views.misc_views import LogoutPageView
from .views.statistics_views import (
    LeaderStatisticsPageView, DPOStatisticsPageView, UserStatisticsPageView,
    EmployeeView)
from .views.report_views import (
    UserReportView, UserArchiveView, RemediatorView, RemediatorArchiveView,
    UndistributedView, UndistributedArchiveView)
from .views.user_views import AccountView, AccountOutlookSettingView
from .views.manual_views import ManualMainView
from .views.support_views import SupportButtonView

urlpatterns = [
    re_path(r'^$',      UserReportView.as_view(),     name="index"),
    re_path(r'^reports$', UserReportView.as_view(), name="reports"),
    re_path(r'^remediator$', RemediatorView.as_view(), name="remediator"),
    re_path(r'^undistributed$', UndistributedView.as_view(), name="undistributed"),
    re_path(r'^archive/reports', UserArchiveView.as_view(), name="reports-archive"),
    re_path(r'^archive/remediator', RemediatorArchiveView.as_view(), name="remediator-archive"),
    re_path(r'^archive/undistributed', UndistributedArchiveView.as_view(),
            name="undistributed-archive"),
    re_path('api$',     JSONAPIView.as_view(),     name="json-api"),
    path('account/<uuid:pk>', AccountView.as_view(), name="account"),
    path('account/', AccountView.as_view(), name="account-me"),
    path("account/outlook-category-settings/", AccountOutlookSettingView.as_view(),
         name="outlook-category-settings"),
    re_path(r'^statistics/leader/$', LeaderStatisticsPageView.as_view(), name='statistics-leader'),
    re_path(r'^statistics/dpo/$', DPOStatisticsPageView.as_view(), name='statistics-dpo'),
    path('statistics/user/', UserStatisticsPageView.as_view(),
         name='statistics-user-me'),
    path('statistics/user/<uuid:pk>', UserStatisticsPageView.as_view(),
         name='statistics-user-id'),
    path('statistics/employee/<uuid:pk>', EmployeeView.as_view(), name='employee'),
    re_path(r'^health/', lambda r: HttpResponse()),
    re_path(r'^version/?$', lambda r: HttpResponse(__version__)),
    re_path(r'^help/$', ManualMainView.as_view(), name="guide"),
    re_path(r'^support/$', SupportButtonView.as_view(), name="support_button"),
    re_path(r'^jsi18n/$',
            JavaScriptCatalog.as_view(
                packages=(['os2datascanner.projects.report.reportapp'])),
            name="jsi18n"),
    path('htmx_endpoints/', include('os2datascanner.projects.report.reportapp.htmx_endpoints_urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.SAML2_ENABLED:
    urlpatterns.append(re_path(r"^saml2_auth/metadata.xml$", metadata, name="saml_metadata"))
    urlpatterns.append(re_path(r"^saml2_auth/", include("django_saml2_auth.urls")))
    urlpatterns.append(re_path(r"^accounts/login/$", django_saml2_auth.views.signin))
    urlpatterns.append(re_path(r'^accounts/logout/$', django_saml2_auth.views.signout))

if settings.KEYCLOAK_ENABLED:
    settings.LOGIN_URL = "oidc_authentication_init"
    settings.LOGOUT_REDIRECT_URL = settings.SITE_URL + "accounts/logout/"
    urlpatterns.append(path('oidc/', include('mozilla_django_oidc.urls'))),
    urlpatterns.append(re_path(r'^accounts/logout/',
                               LogoutPageView.as_view(
                                   template_name='components/user/logout.html',
                                   extra_context={'body_class': 'login-bg'}
                                   ),
                               name='logout'))
else:
    urlpatterns.append(re_path(r'^accounts/login/',
                               django.contrib.auth.views.LoginView.as_view(
                                   template_name='components/user/login.html',
                                   extra_context={'body_class': 'login-bg'}
                                   ),
                               name='login'))
    urlpatterns.append(re_path(r'^accounts/logout/',
                               django.contrib.auth.views.LogoutView.as_view(
                                   template_name='components/user/logout.html',
                                   extra_context={'body_class': 'login-bg'}
                                   ),
                               name='logout'))
    urlpatterns.append(re_path(r'^accounts/password_change/',
                               django.contrib.auth.views.PasswordChangeView.as_view(
                                   template_name='components/password/password_change.html',
                                   ),
                               name='password_change'))
    urlpatterns.append(re_path(r'^accounts/password_change_done/',
                               django.contrib.auth.views.PasswordChangeDoneView.as_view(
                                   template_name='components/password/password_change_done.html',
                                   ),
                               name='password_change_done'))
    urlpatterns.append(re_path(r'^accounts/password_reset/$',
                               django.contrib.auth.views.PasswordResetView.as_view(
                                   template_name='components/password/password_reset_form.html',
                                   ),
                               name='password_reset'))
    urlpatterns.append(re_path(r'^accounts/password_reset/done/',
                               django.contrib.auth.views.PasswordResetDoneView.as_view(
                                   template_name='components/password/password_reset_done.html',
                                   ),
                               name='password_reset_done'))
    urlpatterns.append(re_path(r'^accounts/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/' +
                               '(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]*)/',
                               django.contrib.auth.views.PasswordResetConfirmView.as_view(
                                   template_name='components/password/password_reset_confirm.html',
                                   ),
                               name='password_reset_confirm'))
    urlpatterns.append(re_path(r'^accounts/reset/complete',
                               django.contrib.auth.views.PasswordResetCompleteView.as_view(
                                   template_name='components/password/password_reset_complete.html',
                                   ),
                               name='password_reset_complete'))
