"""
Utility functions to support configuration through toml-files.
"""

import logging
import os
import sys
import toml

from django.utils.translation import gettext_lazy as _

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
    # we cannot just do dict.update, because we do not want to "pollute" the
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
    system_settings = os.getenv(sys_var, None)
    user_settings = os.getenv(user_var, None)

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

    _process_directory_configuration(config, "*", parent_path)
    _process_locales(config, "*", parent_path)
    _set_constants(module, config)

    if globals().get('OPTIONAL_APPS'):
        globals()['INSTALLED_APPS'] += globals()['OPTIONAL_APPS']

