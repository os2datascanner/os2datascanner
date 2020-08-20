"""
Django settings file for OS2datascanner administration module.
"""

import logging
import os
import pathlib
import structlog
import sys
import toml

from django.core.exceptions import ImproperlyConfigured

from django.utils.translation import gettext_lazy as _

# The standard logger is ONLY used during the processing of the TOML files.
# The rest of the application uses structlog, which is set up using some of the
# configuration settings passed in the TOML files

logger = logging.getLogger("configuration")

def read_config(config_path):
    try:
        with open(config_path) as f:
            content = f.read()
    except FileNotFoundError as err:
        logger.critical("%s: %r", err.strerror, err.filename)
        sys.exit(5)
    try:
        return toml.loads(content)
    except toml.TomlDecodeError:
        logger.critical("Failed to parse TOML")
        sys.exit(4)


def update_config(configuration, new_settings):
    # we cannot just do dict.update, because we do not want to "polute" the
    # namespace with anything in *new_settings*, just the variables defined in
    # **configuration**.
    for key in new_settings:
        if key in configuration:
            if isinstance(configuration[key], dict):
                update_config(configuration[key], new_settings[key])
            else:
                configuration[key] = new_settings[key]
        else:
            logger.warning("Invalid key in config: %s", key)

def _process_relative_path(placeholder, replacement_value, path_list):
    if path_list and path_list[0] == placeholder:
        path_list[0] = replacement_value
    return os.path.join(*path_list)


def _set_constants(module, configuration):
    # NEVER print or log the config object, as it will expose secrets
    # Only ever print or log explicitly chosen (and safe!) settings!
    for key, value in configuration.items():
        if key.isupper() and not key.startswith('_'):
            # NB! Never log the value for an unspecified key!
            if isinstance(value, list):
                logger.debug("Converting list value to tuple for %s", key)
                value = tuple(value)
            logger.info("Adding setting: %s", key)
            setattr(module, key, value)

def _process_directory_configuration(configuration, placeholder, directory):
    directories = configuration.get('dirs')
    if not directories:
        raise ImproperlyConfigured(
            "The configuration is missing the required list of directories."
        )
    for key, value in directories.items():
        if configuration.get(key):
            raise ImproperlyConfigured(
                "The directory %s has already been configured" % key
            )
        else:
            configuration[key] = _process_relative_path(
                placeholder, directory, value
            )

def _process_locales(configuration, placeholder, directory, translation_func):
    # Set locale paths
    path_list = configuration.get('_LOCALE_PATHS')
    if path_list:
        configuration['LOCALE_PATHS'] = [
            _process_relative_path(placeholder, directory, path) for path in path_list
        ]
    # Set languages and their localized names
    _ = translation_func
    language_list = configuration.get('_LANGUAGES')
    if language_list:
        configuration['LANGUAGES'] = [
            (language[0], _(language[1])) for language in language_list
        ]

def process_toml_configuration_for_django(project_directory, module):
    # Specify file paths
    settings_dir = os.path.abspath(os.path.dirname(__file__))
    default_settings = os.path.join(settings_dir, 'default-settings.toml')
    system_settings = os.getenv('DSC_ADMIN_SYSTEM_CONFIG_PATH', None)
    user_settings = os.getenv('DSC_ADMIN_USER_CONFIG_PATH', None)

    # Load default configuration
    if not os.path.isfile(default_settings):
        logger.error("Invalid file path for default settings: %s",
                     default_settings)
        sys.exit(1)

    config = read_config(default_settings)
    # Load system configuration
    if system_settings:
        logger.info("Reading system config from %s", system_settings)
        update_config(config, read_config(system_settings))
    # Load user configuration
    if user_settings:
        logger.info("Reading user settings from %s", user_settings)
        update_config(config, read_config(user_settings))

    _process_directory_configuration(config, "*", project_directory)
    _process_locales(config, "*", project_directory, _)
    _set_constants(module, config)

    if globals().get('OPTIONAL_APPS'):
        globals()['INSTALLED_APPS'] += globals()['OPTIONAL_APPS']


BASE_DIR = str(pathlib.Path(__file__).resolve().parent.parent.parent.parent.absolute())
PROJECT_DIR = os.path.dirname(BASE_DIR)

process_toml_configuration_for_django(PROJECT_DIR, sys.modules[__name__])

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

"""
LOCALE_PATHS = (
    os.path.join(PROJECT_DIR, 'locale', 'admin'),
)

LANGUAGES = (
    ('da', _('Danish')),
    ('en', _('English')),
)
"""
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
            "filename": globals()['VAR_DIR'] + '/debug.log',
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

os.makedirs(globals()['BUILD_DIR'], exist_ok=True)
os.makedirs(globals()['MEDIA_ROOT'], exist_ok=True)
