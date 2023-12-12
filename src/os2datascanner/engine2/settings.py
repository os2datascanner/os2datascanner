import logging
from pathlib import Path

from os2datascanner.utils.toml_configuration import (
        TrivialLogger, get_3_layer_config)


logger = TrivialLogger(__name__)


# NEVER print or log the config object, as it will expose secrets
# Only ever print or log explicitly chosen (and safe!) settings!
for key, value in get_3_layer_config(
        Path(__file__).parent.joinpath("default-settings.toml"),
        "OS2DS_ENGINE_SYSTEM_CONFIG_PATH",
        "OS2DS_ENGINE_USER_CONFIG_PATH").items():
    if not key.startswith('_'):
        # NB! Never log the value for an unspecified key!
        if isinstance(value, list):
            logger.debug("converting list value to tuple for %s", key)
            value = tuple(value)
        logger.debug("adding setting: %s", key)
        globals()[key] = value


del key, Path, value, logger, logging, get_3_layer_config
