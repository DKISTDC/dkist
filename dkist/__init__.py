import os
from warnings import warn

from pkg_resources import DistributionNotFound, get_distribution

from astropy.config.configuration import (ConfigurationDefaultMissingError,
                                          ConfigurationDefaultMissingWarning,
                                          update_default_config)
from astropy.tests.helper import TestRunner

from .dataset import Dataset  # noqa

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = "unknown"

# add these here so we only need to cleanup the namespace at the end
config_dir = None

if not os.environ.get('ASTROPY_SKIP_CONFIG_UPDATE', False):
    config_dir = os.path.dirname(__file__)
    config_template = os.path.join(config_dir, __package__ + ".cfg")
    if os.path.isfile(config_template):
        try:
            update_default_config(
                __package__, config_dir, version=__version__)
        except TypeError as orig_error:
            try:
                update_default_config(__package__, config_dir)
            except ConfigurationDefaultMissingError as e:
                wmsg = (e.args[0] +
                        " Cannot install default profile. If you are "
                        "importing from source, this is expected.")
                warn(ConfigurationDefaultMissingWarning(wmsg))
                del e
            except Exception:
                raise orig_error


__all__ = ['test', 'Dataset']

test = TestRunner.make_test_runner_in(os.path.dirname(__file__))
