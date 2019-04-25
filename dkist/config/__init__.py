from astropy.config import ConfigNamespace, ConfigItem as _AstropyConfigItem


__all__ = ['ConfigItem', 'ConfigNamespace']


class ConfigItem(_AstropyConfigItem):
    rootname = 'dkist'
