from astropy.config import ConfigItem as _AstropyConfigItem
from astropy.config import ConfigNamespace

__all__ = ["ConfigItem", "ConfigNamespace"]


# We can't use this subclass because of the bug fixed in https://github.com/astropy/astropy/pull/18107
# this can be put back when we are min astropy 7.0.2
# class ConfigNamespace(_AstropyConfigNamespace):
#     rootname = "dkist"


class ConfigItem(_AstropyConfigItem):
    rootname = "dkist"
