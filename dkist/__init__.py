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


def write_default_config(overwrite=False):
    """
    Writes out the template configuration file for this version of dkist.

    This function will save a template config file for manual editing, if a
    config file already exits this will write a config file appended with the
    version number, to facilitate comparison of changes.
    """
    return _config.create_config_file("dkist", "dkist", overwrite=overwrite)
