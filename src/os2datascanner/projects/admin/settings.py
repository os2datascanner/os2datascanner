"""
Django settings file for OS2datascanner administration project.

"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import pathlib
import structlog

from django.utils.translation import gettext_lazy as _

# The URL of this site, used in links in emails and in the redirect URL for
# OAuth 2.0 services. (This value should end with a forward slash.)
SITE_URL = '*'

BASE_DIR = str(pathlib.Path(__file__).resolve().parent.parent.parent.parent.absolute())
PROJECT_DIR = os.path.dirname(BASE_DIR)
BUILD_DIR = os.path.join(PROJECT_DIR, 'build')
VAR_DIR = os.path.join(PROJECT_DIR, 'var')
LOGS_DIR = os.path.join(VAR_DIR, 'logs')
MEDIA_ROOT = os.path.join(PROJECT_DIR, 'uploads', 'admin')

# Local settings file shall be used for debugging.
DEBUG = False

# (Allow SECRET_KEY to be overridden by a CI environment variable)
SECRET_KEY = os.getenv("SECRET_KEY", "")

# The GUID of the registered Azure application corresponding to this
# OS2datascanner installation, used when requesting Microsoft Graph access
MSGRAPH_APP_ID = None

# The client secret used to demonstrate to Microsoft Graph that this
# OS2datascanner installation corresponds to a registered Azure application
# (client private keys are not yet supported)
MSGRAPH_CLIENT_SECRET = None

# Add settings here to make them accessible from templates
SETTINGS_EXPORT = [
    'DEBUG',
    'ENABLE_FILESCAN',
    'ENABLE_EXCHANGESCAN',
    'ENABLE_WEBSCAN',
    'ENABLE_DROPBOXSCAN',
    'ENABLE_MSGRAPH_MAILSCAN',
    'ENABLE_MSGRAPH_FILESCAN',
    'ICON_SPRITE_URL'
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django_settings_export.settings_export',
            ],
        },
    },
]

TEST_RUNNER = 'xmlrunner.extra.djangotestrunner.XMLTestRunner'
TEST_OUTPUT_FILE_NAME = os.path.join(BUILD_DIR, 'test-results.xml')
TEST_OUTPUT_DESCRIPTIONS = True
TEST_OUTPUT_VERBOSE = True

AMQP_HOST = os.getenv("AMQP_HOST", "localhost")

# The name of the AMQP queue that the engine2 pipeline expects input on
AMQP_PIPELINE_TARGET = "os2ds_scan_specs"

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'os2datascanner.projects.admin.adminapp.apps.AdminappConfig',
    'recurrence',
)

try:
    # if installed, add django_extensions for its many useful commands
    import django_extensions  # noqa

    INSTALLED_APPS += (
        'django_extensions',
    )
except ImportError:
    pass

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_structlog.middlewares.RequestMiddleware',
)

ROOT_URLCONF = 'os2datascanner.projects.admin.urls'

WSGI_APPLICATION = 'os2datascanner.projects.admin.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'os2datascanner_admin',
        'USER': 'os2datascanner_admin',
        'PASSWORD': 'os2datascanner_admin',
        'HOST': os.getenv('POSTGRES_HOST', '127.0.0.1'),
    }
}

DATABASE_POOL_ARGS = {
    'max_overflow': 10,
    'pool_size': 5,
    'recycle': 300
}

# Internationalization

LANGUAGE_CODE = 'da-dk'

LOCALE_PATHS = (
    os.path.join(PROJECT_DIR, 'locale', 'admin'),
)

LANGUAGES = (
    ('da', _('Danish')),
    ('en', _('English')),
)

TIME_ZONE = 'Europe/Copenhagen'

USE_I18N = True

USE_L10N = True

USE_TZ = True

USE_THOUSAND_SEPARATOR = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR,
        'os2datascanner', 'projects', 'static', 'admin')
AUTH_PROFILE_MODULE = 'os2datascanner.projects.admin.adminapp.UserProfile'
ICON_SPRITE_URL = '/static/src/svg/symbol-defs.svg'

LOGIN_REDIRECT_URL = '/'

# Email  settings
# Email  settings
DEFAULT_FROM_EMAIL = '(Magenta Info) info@magenta.dk'
ADMIN_EMAIL = '(Magenta Admin) info@magenta.dk'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

NOTIFICATION_INSTITUTION = None

# Enable groups - or not

DO_USE_GROUPS = False

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': (
            'django.contrib.auth.password_validation'
            '.UserAttributeSimilarityValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation'
            '.MinimumLengthValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation'
            '.CommonPasswordValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation'
            '.NumericPasswordValidator'
        ),
    },
]


# Hostname to use for logging to Graylog; its absence supresses such
# logging

GRAYLOG_HOST = os.getenv('DJANGO_GRAYLOG_HOST')

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=structlog.threadlocal.wrap_dict(dict),
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


# Logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        "gelf": {
            "()": "os2datascanner.utils.gelf.GELFFormatter",
        },
        "json": {
            "()": "structlog.stdlib.ProcessorFormatter",
            "processor": structlog.processors.JSONRenderer(),
        },
        "console": {
            "()": "structlog.stdlib.ProcessorFormatter",
            "processor": structlog.dev.ConsoleRenderer(),
        },
        "key_value": {
            "()": "structlog.stdlib.ProcessorFormatter",
            "processor": structlog.processors.KeyValueRenderer(key_order=[
                'timestamp',
                'level',
                'event',
                'logger',
            ]),
        },
        'verbose': {
            'format': (
                '%(levelname)s %(asctime)s %(module)s %(process)d '
                '%(thread)d %(message)s'
            ),
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        "requires_graylog_host": {
            "()": "django.utils.log.CallbackFilter",
            "callback": lambda record: bool(GRAYLOG_HOST),
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            'filters': ['require_debug_true'],
            "formatter": "console",
        },
        "debug_log": {
            "level": "DEBUG",
            "class": "logging.handlers.WatchedFileHandler",
            "filename": VAR_DIR + '/debug.log',
            'filters': ['require_debug_true'],
            "formatter": "key_value",
        },
        "graylog": {
            "level": "DEBUG",
            "class": "os2datascanner.utils.gelf.GraylogDatagramHandler",
            "host": GRAYLOG_HOST,
            "filters": ["requires_graylog_host"],
            "formatter": "gelf",
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django_structlog': {
            'handlers': ['console', 'debug_log', 'graylog'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
        'os2datascanner': {
            'handlers': ['console', 'debug_log', 'graylog'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
    }
}

# Enable Dropbox scans for this installation?
ENABLE_DROPBOXSCAN = False

# Enable Microsoft Graph mail scans for this installation?
ENABLE_MSGRAPH_MAILSCAN = False

# Enable Microsoft Graph file scans for this installation?
ENABLE_MSGRAPH_FILESCAN = False

local_settings_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'local_settings.py'
)
if os.path.exists(local_settings_file):
    from .local_settings import *  # noqa

os.makedirs(BUILD_DIR, exist_ok=True)
os.makedirs(MEDIA_ROOT, exist_ok=True)
