"""
This module provides some (partial) sample datasets.
"""

from ._sample import _SAMPLE_DATASETS, VISP_HEADER, _get_sample_datasets

__all__ = ["download_all_sample_data", *sorted(_SAMPLE_DATASETS.keys()), "VISP_HEADER"]  # noqa: PLE0604


# See PEP 562 (https://peps.python.org/pep-0562/) for module-level __dir__()
def __dir__():
    return __all__


# See PEP 562 (https://peps.python.org/pep-0562/) for module-level __getattr__()
def __getattr__(name):
    if name in _SAMPLE_DATASETS:
        return _get_sample_datasets(name)[0]

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def download_all_sample_data():
    """
    Download all sample data at once that has not already been downloaded.
    """
    return _get_sample_datasets(_SAMPLE_DATASETS.keys())
