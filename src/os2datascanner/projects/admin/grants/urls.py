from django.http import HttpResponse
from django.urls import path

from os2datascanner.projects.admin.grants.views import msgraph_views


urlpatterns = [
    path('msgraph/receive/',
            msgraph_views.MSGraphGrantReceptionView.as_view(),
            name='msgraphgrant-receive'),
]
