"""
The DKIST package aims to help you search, obtain and use DKIST data as part of your Python software.
"""
from pkg_resources import DistributionNotFound, get_distribution

import astropy.config as _config

from .dataset import Dataset, TiledDataset  # noqa
from .utils.sysinfo import system_info  # noqa

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = "unknown"

__all__ = ['TiledDataset', 'Dataset', 'system_info']


def write_default_config():
    """
    Writes out the template configuration file for this version of dkist.

    This function will save a template config file for manual editing, if a
    config file already exits this will write a config file appended with the
    version number, to facilitate comparison of changes.

    Returns
    -------
    filepath : `pathlib.Path` or `None`
        The full path of the file written or `None` if no file was written.
    """
    return _config.write_default_config("dkist", "dkist")
