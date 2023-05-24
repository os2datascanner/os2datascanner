"""Django module for the OS2datascanner project."""
import django


if django.VERSION >= (3, 2):
    pass
else:
    default_app_config = 'adminapp.apps.AdminappConfig'
