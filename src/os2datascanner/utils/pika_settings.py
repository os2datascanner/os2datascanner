import logging
import os

from enum import Enum

from os2datascanner.utils.toml_configuration import get_3_layer_config

logger = logging.getLogger(__file__)


class DscModule(Enum):
    ADMIN = ('admin',)
    ENGINE = ('engine',)
    REPORT = ('report',)

    @classmethod
    def determine_dsc_module(cls):
        # TODO: Consider a more elegant way to determine this
        if os.getenv('DSC_ADMIN_SYSTEM_CONFIG_PATH'):
            return cls.ADMIN
        if os.getenv('DSC_ENGINE_SYSTEM_CONFIG_PATH'):
            return cls.ENGINE
        if os.getenv('DSC_REPORT_SYSTEM_CONFIG_PATH'):
            return cls.REPORT

    def __init__(self, _):
        self.sys_var = f"DSC_{self.name}_SYSTEM_CONFIG_PATH"
        self.user_var = f"DSC_{self.name}_USER_CONFIG_PATH"


def _get_default_settings_path(dsc_module):
    project_dir = os.path.abspath(
        os.path.dirname(
            os.path.dirname(__file__)
        )
    )
    path = project_dir
    if dsc_module == DscModule.ENGINE:
        path = os.path.join(project_dir, 'engine2')
    elif dsc_module == DscModule.ADMIN:
        path = os.path.join(project_dir, 'projects', 'admin')
    elif dsc_module == DscModule.REPORT:
        path = os.path.join(project_dir, 'projects', 'report')
    return os.path.join(path, 'default-settings.toml')


def _get_config(key=None):
    dsc_module = DscModule.determine_dsc_module()
    default_settings = _get_default_settings_path(dsc_module)
    config = get_3_layer_config(default_settings,
                                sys_var=dsc_module.sys_var,
                                user_var=dsc_module.user_var)
    if key:
        config = config[key]
    return config


_config = _get_config('amqp')
AMQP_HOST = _config['AMQP_HOST']
AMQP_USER = _config['AMQP_USER']
AMQP_PWD = _config['AMQP_PWD']
