from astropy.config import ConfigItem as _AstropyConfigItem
from astropy.config import ConfigNamespace as _AstropyConfigNamespace

__all__ = ['ConfigItem', 'ConfigNamespace']


class ConfigNamespace(_AstropyConfigNamespace):
    rootname = 'dkist'


class ConfigItem(_AstropyConfigItem):
    rootname = 'dkist'
