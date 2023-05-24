import django


if django.VERSION >= (3, 2):
    pass
else:
    default_app_config = 'grants.apps.GrantsConfig'
