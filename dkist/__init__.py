"""
The DKIST package aims to help you search, obtain and use DKIST data as part of your Python software.
"""
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

import platformdirs as _platformdirs

from .logger import setup_default_dkist_logger as _setup_log
import dkist.config as _config

log = _setup_log(__name__)

try:
    __version__ = _version(__name__)
except PackageNotFoundError:
    __version__ = "unknown"


__all__ = ["Dataset", "TiledDataset", "conf", "load_dataset", "system_info"]


def write_default_config(overwrite=False):
    """
    Writes out the template configuration file for this version of dkist.

    This function will save a template config file for manual editing, if a
    config file already exits this will write a config file appended with the
    version number, to facilitate comparison of changes.
    """
    import astropy.config as _config
    return _config.create_config_file("dkist", "dkist", overwrite=overwrite)


class Conf(_config.ConfigNamespace):
    """
    Configuration Parameters for the `dkist` Package.
    """
    sample_data_directory = _config.ConfigItem(
        _platformdirs.user_data_dir(appname="dkist"),
        "Location to download sample data to."
    )


conf = Conf()


# Do internal imports last (so logger etc is initialised)
from dkist.dataset import Dataset, TiledDataset, load_dataset
from dkist.utils.sysinfo import system_info
