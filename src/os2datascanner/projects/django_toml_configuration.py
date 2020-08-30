"""
Utility functions to support configuration through toml-files for Django.
"""

import logging
import os
import sys

from django.utils.translation import gettext_lazy as _

from os2datascanner.utils.toml_configuration import get_3_layer_config

logger = logging.getLogger(__file__)


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
        logger.error(
            "The configuration is missing the required list of directories."
        )
        sys.exit(1)
    for key, value in directories.items():
        if configuration.get(key):
            logger.error(
                "The directory %s has already been configured" % key
            )
            sys.exit(1)
        else:
            configuration[key] = _process_relative_path(
                placeholder, directory, value
            )


def _process_locales(configuration, placeholder, directory):
    # Set locale paths
    path_list = configuration.get('_LOCALE_PATHS')
    if path_list:
        configuration['LOCALE_PATHS'] = [
            _process_relative_path(placeholder, directory, path) for path in path_list
        ]
    # Set languages and their localized names
    language_list = configuration.get('_LANGUAGES')
    if language_list:
        configuration['LANGUAGES'] = [
            (language[0], _(language[1])) for language in language_list
        ]


def process_toml_conf_for_django(parent_path, module, sys_var, user_var):
    # Specify file paths
    settings_dir = os.path.abspath(os.path.dirname(module.__file__))
    default_settings = os.path.join(settings_dir, 'default-settings.toml')

    config = get_3_layer_config(default_settings, sys_var, user_var)

    _process_directory_configuration(config, "*", parent_path)
    _process_locales(config, "*", parent_path)
    _set_constants(module, config)

    if globals().get('OPTIONAL_APPS'):
        globals()['INSTALLED_APPS'] += globals()['OPTIONAL_APPS']

