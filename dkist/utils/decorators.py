from astropy.utils.decorators import deprecated as astropy_deprecated

from .exceptions import DKISTDeprecationWarning


def deprecated(*args, **kwargs):
    return astropy_deprecated(*args, warning_type=DKISTDeprecationWarning, **kwargs)
