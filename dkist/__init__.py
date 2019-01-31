from pkg_resources import get_distribution, DistributionNotFound

from ._dkist_init import *  # noqa

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = "unknown"

if not _ASTROPY_SETUP_:  # noqa
    # For egg_info test builds to pass, put package imports here.
    from .dataset import Dataset  # noqa
