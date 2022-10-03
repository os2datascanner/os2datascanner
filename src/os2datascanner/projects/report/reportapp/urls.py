import django_saml2_auth.views
import django.contrib.auth.views
from django.conf.urls import url
from django.http import HttpResponse
from django.urls import include
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path
from os2datascanner import __version__

from .views.api import JSONAPIView
from .views.saml import metadata
from .views.views import (
    MainPageView, LeaderStatisticsPageView,
    DPOStatisticsPageView, ApprovalPageView,
    StatsPageView, SettingsPageView, AboutPageView, LogoutPageView)
from .views.user_views import UserView

urlpatterns = [
    url(r'^$',      MainPageView.as_view(),     name="index"),
    url(r'^content', MainPageView.as_view(), name="content"),
    url('api$',     JSONAPIView.as_view(),     name="json-api"),
    url(r'^user/', UserView.as_view(), name="user"),
    url(r'^statistics/leader/$', LeaderStatisticsPageView.as_view(), name='statistics'),
    url(r'^statistics/dpo/$', DPOStatisticsPageView.as_view(), name='statistics'),
    url('approval', ApprovalPageView.as_view(), name="about"),
    url('stats',    StatsPageView.as_view(),    name="about"),
    url('settings', SettingsPageView.as_view(), name="settings"),
    url('about',    AboutPageView.as_view(),    name="about"),
    url(r'^health/', lambda r: HttpResponse()),
    url(r'^version/?$', lambda r: HttpResponse(__version__)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.SAML2_ENABLED:
    urlpatterns.append(url(r"^saml2_auth/metadata.xml$", metadata, name="saml_metadata"))
    urlpatterns.append(url(r"^saml2_auth/", include("django_saml2_auth.urls")))
    urlpatterns.append(url(r"^accounts/login/$", django_saml2_auth.views.signin))
    urlpatterns.append(url(r'^accounts/logout/$', django_saml2_auth.views.signout))

if settings.KEYCLOAK_ENABLED:
    settings.LOGIN_URL = "oidc_authentication_init"
    settings.LOGOUT_REDIRECT_URL = settings.SITE_URL + "accounts/logout/"
    urlpatterns.append(path('oidc/', include('mozilla_django_oidc.urls'))),
    urlpatterns.append(url(r'^accounts/logout/',
                           LogoutPageView.as_view(
                               template_name='logout.html',
                               extra_context={'body_class': 'login-bg'}
                           ),
                           name='logout'))
else:
    urlpatterns.append(url(r'^accounts/login/',
                           django.contrib.auth.views.LoginView.as_view(
                               template_name='login.html',
                               extra_context={'body_class': 'login-bg'}
                           ),
                           name='login'))
    urlpatterns.append(url(r'^accounts/logout/',
                           django.contrib.auth.views.LogoutView.as_view(
                               template_name='logout.html',
                               extra_context={'body_class': 'login-bg'}
                           ),
                           name='logout'))
    urlpatterns.append(url(r'^accounts/password_change/',
                           django.contrib.auth.views.PasswordChangeView.as_view(
                               template_name='password_change.html',
                           ),
                           name='password_change'))
    urlpatterns.append(url(r'^accounts/password_change_done/',
                           django.contrib.auth.views.PasswordChangeDoneView.as_view(
                               template_name='password_change_done.html',
                           ),
                           name='password_change_done'))
    urlpatterns.append(url(r'^accounts/password_reset/$',
                           django.contrib.auth.views.PasswordResetView.as_view(
                               template_name='password_reset_form.html',
                           ),
                           name='password_reset'))
    urlpatterns.append(url(r'^accounts/password_reset/done/',
                           django.contrib.auth.views.PasswordResetDoneView.as_view(
                               template_name='password_reset_done.html',
                           ),
                           name='password_reset_done'))
    urlpatterns.append(url(r'^accounts/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/' +
                           '(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]*)/',
                           django.contrib.auth.views.PasswordResetConfirmView.as_view(
                               template_name='password_reset_confirm.html',
                           ),
                           name='password_reset_confirm'))
    urlpatterns.append(url(r'^accounts/reset/complete',
                           django.contrib.auth.views.PasswordResetCompleteView.as_view(
                               template_name='password_reset_complete.html',
                           ),
                           name='password_reset_complete'))
