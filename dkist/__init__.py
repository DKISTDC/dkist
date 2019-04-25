import os

from pkg_resources import DistributionNotFound, get_distribution

import astropy.config as _config
from astropy.tests.helper import TestRunner

from .dataset import Dataset  # noqa

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = "unknown"

__all__ = ['test', 'Dataset', 'write_default_config']


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


test = TestRunner.make_test_runner_in(os.path.dirname(__file__))
