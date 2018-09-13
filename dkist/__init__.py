# Licensed under a 3-clause BSD style license - see LICENSE.rst

# Packages may add whatever they like to this file, but
# Enforce Python version check during package import.
# This is the same check as the one at the top of setup.py
import sys

from ._dkist_init import *

__minimum_python_version__ = "3.6"

class UnsupportedPythonError(Exception):
    pass

if sys.version_info < tuple((int(val) for val in __minimum_python_version__.split('.'))):
    raise UnsupportedPythonError("dkist does not support Python < {}".format(__minimum_python_version__))  # pragma: no cover

if not _ASTROPY_SETUP_:
    # For egg_info test builds to pass, put package imports here.
    pass
