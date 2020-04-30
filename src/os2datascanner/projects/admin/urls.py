"""URL patterns."""

from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    # Include webscanner URLs
    url(r'^', include('os2datascanner.projects.admin.adminapp.urls')),
    # Enable admin
    url('^admin/', admin.site.urls),
]
