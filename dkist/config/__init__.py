from astropy.config import ConfigItem as _AstropyConfigItem
from astropy.config import ConfigNamespace

__all__ = ['ConfigItem', 'ConfigNamespace']


class ConfigItem(_AstropyConfigItem):
    rootname = 'dkist'
