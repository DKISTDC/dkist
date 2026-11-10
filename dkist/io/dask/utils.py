import numbers
import uuid
import warnings

import dask
import numpy as np
from packaging.version import Version

import astropy

from dkist.utils.exceptions import DKISTDeprecationWarning

__all__ = ["stack_loader_array"]


def _combine_slices(slice1, slice2):
    """
    Given two slices that can be applied to a 1-d array, find the resulting
    slice that corresponds to the combination of both slices. We assume that
    slice2 can be an integer, but slice1 cannot.
    """
    if isinstance(slice1, slice) and slice1.step not in (None, 1):
        raise ValueError("Only slices with steps of 1 are supported")

    if isinstance(slice2, slice) and slice2.step not in (None, 1):
        raise ValueError("Only slices with steps of 1 are supported")

    if isinstance(slice2, numbers.Integral):
        if slice1.start is None:
            return slice2
        else:  # noqa RET505
            return slice2 + slice1.start

    if slice1.start is None:
        if slice1.stop is None:
            return slice2
        else:  # noqa RET505
            if slice2.stop is None:
                return slice(slice2.start, slice1.stop)
            else:  # noqa RET505
                return slice(slice2.start, min(slice1.stop, slice2.stop))
    else:
        if slice2.start is None:
            start = slice1.start
        else:
            start = slice1.start + slice2.start
        if slice2.stop is None:
            stop = slice1.stop
        else:
            if slice1.start is None:
                stop = slice2.stop
            else:
                stop = slice2.stop + slice1.start
            if slice1.stop is not None:
                stop = min(slice1.stop, stop)
    return slice(start, stop)


# combine_slices was fixed to accept an explicit step of 1 in astropy 7.2.3
# (backported to 8.0.2); use the vendored copy on versions that lack the fix.
_astropy_version = Version(astropy.__version__)
if _astropy_version < Version("7.2.3") or (
    Version("8.0.0") <= _astropy_version < Version("8.0.2")
):
    combine_slices = _combine_slices
else:
    from astropy.wcs.wcsapi.wrappers.sliced_wcs import combine_slices  # noqa F401


def stack_loader_array(loader_array, output_shape, chunksize=None):
    """
    Converts an array of loaders to a dask array that loads a chunk from each loader

    This results in a dask array with the correct chunks and dimensions.

    Parameters
    ----------
    loader_array : `dkist.io.loaders.BaseFITSLoader`
        An array of loader objects
    output_shape : tuple[int]
        The intended shape of the final array
    chunksize : tuple[int]
        Can be used to set a chunk size. If not provided, each batch is one chunk

    Returns
    -------
    array : `dask.array.Array`
    """
    file_shape = loader_array.flat[0].shape

    # Dask identifies arrays by their name, so the name has to be unique to
    # this array: if two arrays share a name, combining them into a single
    # graph (for example stacking two tiles of a mosaic) silently uses one
    # array's tasks for both.
    name = f"load_files-{uuid.uuid4().hex}"

    tasks = {}
    for i, loader in enumerate(loader_array.flat):
        # The key identifies this chunk's position in the (partially-flattened) final data cube
        key = (name, i)
        key += (0,) * len(file_shape)
        # Each task will be to call _call_loader, with the loader as an argument
        tasks[key] = (_call_loader, loader)

    dsk = dask.highlevelgraph.HighLevelGraph.from_collections(name, tasks, dependencies=())
    # Specifies that each chunk occupies a space of 1 pixel in the first dimension, and all the pixels in the others
    chunks = (*((1,) * loader_array.size,), *((s,) for s in file_shape))
    array = dask.array.Array(dsk,
                             name=name,
                             chunks=chunks,
                             dtype=loader_array.flat[0].dtype)
    # Now impose the higher dimensions on the data cube
    array = array.reshape(output_shape)
    if chunksize is not None:
        warnings.warn("Using the dask file loader with a non-default chunksize is deprecated. "
                      "If you see this warning loading an ASDF file please open an issue "
                      "on GitHub: https://github.com/DKISTDC/dkist/issues", DKISTDeprecationWarning)
        # If requested, re-chunk the array. Not sure this is optimal
        new_chunks = (1,) * (array.ndim - len(chunksize)) + chunksize
        array = array.rechunk(new_chunks)
    return array


def _call_loader(loader):
    data = loader.data
    # The data needs an extra dimension for the leading index of the intermediate data cube, which has a leading
    # index for file number
    return np.expand_dims(data, 0)
