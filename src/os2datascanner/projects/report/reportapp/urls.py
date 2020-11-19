import django_saml2_auth.views
from django.conf.urls import url
from django.http import HttpResponse
from django.urls import include
from django.conf import settings
from django.urls import path
from .views.api import JSONAPIView
from .views.views import (MainPageView, StatisticsPageView, ApprovalPageView,
                          StatsPageView, SettingsPageView, AboutPageView, LogoutPageView)

urlpatterns = [
    url(r'^$',      MainPageView.as_view(),     name="index"),
    url('api$',     JSONAPIView.as_view(),     name="json-api"),
    url('statistics', StatisticsPageView.as_view(), name="statistics"),
    url('approval', ApprovalPageView.as_view(), name="about"),
    url('stats',    StatsPageView.as_view(),    name="about"),
    url('settings', SettingsPageView.as_view(), name="settings"),
    url('about',    AboutPageView.as_view(),    name="about"),
    url(r'^health/', lambda r: HttpResponse()),
    path('oidc/', include('mozilla_django_oidc.urls')),
]

if settings.SAML2_ENABLED:
    urlpatterns.append(url(r"^saml2_auth/", include("django_saml2_auth.urls")))
    urlpatterns.append(url(r"^accounts/login/$", django_saml2_auth.views.signin))
    urlpatterns.append(url(r'^accounts/logout/$', django_saml2_auth.views.signout))
else:
    urlpatterns.append(url(r'^accounts/logout/',
        LogoutPageView.as_view(
            template_name='logout.html',
        ),
        name='logout'))

