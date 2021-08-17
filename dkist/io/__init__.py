"""
Functionality for loading many DKIST FITS files into a single Dask array.
"""
import dkist.config as _config

from .file_manager import FileManager

__all__ = ['FileManager', 'conf']


class Conf(_config.ConfigNamespace):
    """
    Configuration Parameters for the IO Package.
    """

    preferred_fits_library = _config.ConfigItem('astropy',
                                                "Name of the preferred FITS module.")


conf = Conf()
