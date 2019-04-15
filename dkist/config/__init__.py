import astropy.config as astropyconfig


class ConfigNamespace(astropyconfig.ConfigNamespace):
    rootname = 'dkist'


class ConfigItem(astropyconfig.ConfigItem):
    rootname = 'dkist'
