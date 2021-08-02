from functools import partial

import dask.array as da
import numpy as np

__all__ = ['stack_loader_array']


def stack_loader_array(loader_array):
    """
    Stack a loader array along each of its dimensions.

    This results in a dask array with the correct chunks and dimensions.

    Parameters
    ----------
    loader_array : `dkist.io.reference_collections.BaseFITSArrayContainer`

    Returns
    -------
    array : `dask.array.Array`
    """
    if len(loader_array.shape) == 1:
        return da.stack(loader_to_dask(loader_array))
    stacks = []
    for i in range(loader_array.shape[0]):
        stacks.append(stack_loader_array(loader_array[i]))
    return da.stack(stacks)


def loader_to_dask(loader_array):
    """
    Map a call to `dask.array.from_array` onto all the elements in ``loader_array``.

    This is done so that an explicit ``meta=`` argument can be provided to
    prevent loading data from disk.
    """

    if len(loader_array.shape) != 1:
        raise ValueError("Can only be used on one dimensional arrays")

    # The meta argument to from array is used to determine properties of the
    # array, such as dtype. We explicitly specify it here to prevent dask
    # trying to auto calculate it by reading from the actual array on disk.
    meta = np.zeros((0,), dtype=loader_array[0].dtype)

    to_array = partial(da.from_array, meta=meta)

    return map(to_array, loader_array)
