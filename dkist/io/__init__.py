import dkist.config as _config

from .array_collections import (BaseFITSArrayCollection, DaskFITSArrayCollection,
                               NumpyFITSArrayCollection)
from .loaders import AstropyFITSLoader, BaseFITSLoader

__all__ = ['BaseFITSLoader', 'AstropyFITSLoader', 'BaseFITSArrayCollection',
           'NumpyFITSArrayCollection', 'DaskFITSArrayCollection', 'conf']


class Conf(_config.ConfigNamespace):
    """
    Configuration Parameters for the IO Package.
    """

    preferred_fits_library = _config.ConfigItem('astropy',
                                                "Name of the preferred FITS module.")


conf = Conf()
