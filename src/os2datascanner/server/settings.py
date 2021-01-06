import logging
from pathlib import Path

from os2datascanner.utils.toml_configuration import get_3_layer_config


logger = logging.getLogger(__name__)


# NEVER print or log the config object, as it will expose secrets
# Only ever print or log explicitly chosen (and safe!) settings!
for key, value in get_3_layer_config(
        Path(__file__).parent.joinpath("default-settings.toml"),
        "OS2DS_SERVER_SYSTEM_CONFIG_PATH",
        "OS2DS_SERVER_USER_CONFIG_PATH").items():
    if not key.startswith('_'):
        # NB! Never log the value for an unspecified key!
        if isinstance(value, list):
            logger.debug("Converting list value to tuple for %s", key)
            value = tuple(value)
        logger.info("Adding setting: %s", key)
        globals()[key] = value


del key, Path, value, logger, logging, get_3_layer_config
