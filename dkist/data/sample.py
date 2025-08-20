"""
This module provides some (partial) sample datasets.
"""
import warnings as _warnings

from dkist.utils.exceptions import DKISTDeprecationWarning as _DKISTDeprecationWarning

from ._sample import _DEPRECATED_NAMES, _SAMPLE_DATASETS, VISP_HEADER, _get_sample_datasets

__all__ = ["download_all_sample_data", *sorted(_SAMPLE_DATASETS.keys()), *sorted(_DEPRECATED_NAMES.keys()), "VISP_HEADER"]  # noqa: PLE0604


# See PEP 562 (https://peps.python.org/pep-0562/) for module-level __dir__()
def __dir__():
    return __all__


# See PEP 562 (https://peps.python.org/pep-0562/) for module-level __getattr__()
def __getattr__(name):
    if name in _SAMPLE_DATASETS:
        return _get_sample_datasets(name)[0]

    if name in _DEPRECATED_NAMES:
        new_name = _DEPRECATED_NAMES[name]
        _warnings.warn(
            f"The sample data name {name} is deprecated and has been replaced by {new_name}.",
            _DKISTDeprecationWarning,
        )
        return _get_sample_datasets(new_name)[0]

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def download_all_sample_data(overwrite=False):
    """
    Download all sample data at once that has not already been downloaded.

    Parameters
    ----------
    overwrite : `bool`
        Re-download and overwrite any existing files.
    """
    return _get_sample_datasets(_SAMPLE_DATASETS.keys(), force_download=not overwrite)
