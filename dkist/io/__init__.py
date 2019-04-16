import dkist.config as _config

from .fits import AstropyFITSLoader, BaseFITSLoader
from .reference_collections import (BaseFITSArrayContainer,
                                    DaskFITSArrayContainer,
                                    NumpyFITSArrayContainer)

__all__ = ['BaseFITSLoader', 'AstropyFITSLoader', 'BaseFITSArrayContainer',
           'NumpyFITSArrayContainer', 'DaskFITSArrayContainer', 'conf']


class Conf(_config.ConfigNamespace):
    """
    Configuration Parameters for the IO Package.
    """

    preferred_fits_library = _config.ConfigItem('astropy',
                                                "Name of the preferred FITS module.")


conf = Conf()
