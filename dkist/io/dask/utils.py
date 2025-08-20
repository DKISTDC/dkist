import warnings

import dask
import numpy as np

from dkist.utils.exceptions import DKISTDeprecationWarning

__all__ = ["stack_loader_array"]


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

    tasks = {}
    for i, loader in enumerate(loader_array.flat):
        # The key identifies this chunk's position in the (partially-flattened) final data cube
        key = ("load_files", i)
        key += (0,) * len(file_shape)
        # Each task will be to call _call_loader, with the loader as an argument
        tasks[key] = (_call_loader, loader)

    dsk = dask.highlevelgraph.HighLevelGraph.from_collections("load_files", tasks, dependencies=())
    # Specifies that each chunk occupies a space of 1 pixel in the first dimension, and all the pixels in the others
    chunks = (*((1,) * loader_array.size,), *((s,) for s in file_shape))
    array = dask.array.Array(dsk,
                             name="load_files",
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
