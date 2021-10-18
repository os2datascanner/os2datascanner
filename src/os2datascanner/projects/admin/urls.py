"""URL patterns."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

admin.autodiscover()

_active_apps = [
    app.split('.')[3] for app in settings.INSTALLED_APPS
    if app.startswith('os2datascanner')
]

urlpatterns = [
    # Include webscanner URLs
    path('', include('os2datascanner.projects.admin.adminapp.urls'))
]
# Conditionally include urls for relevant active os2datascanner apps:
if 'organizations' in _active_apps:
    urlpatterns.append(path('organizations/', include('organizations.urls')))
if 'import_services' in _active_apps:
    urlpatterns.append(path('imports/', include('import_services.urls')))
if (hasattr(settings, "OPTIONAL_APPS") and "debug_toolbar" in settings.OPTIONAL_APPS):
    import debug_toolbar
    urlpatterns.append(path('__debug__/', include(debug_toolbar.urls))),

# Enable admin
urlpatterns.append(path('admin/', admin.site.urls))
