from itertools import batched

import dask
import numpy as np

__all__ = ["stack_loader_array"]


def stack_loader_array(loader_array, chunksize=None, batch_size=1):
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
    # If the chunksize isn't specified then use the whole array shape
    chunksize = chunksize or loader_array.flat[0].shape
    file_shape = loader_array.flat[0].shape

    tasks = {}
    batches = list(batched(loader_array.flat, batch_size))
    for i, loaders in enumerate(batches):
        key = ("load_files", i)
        key += (0,) * len(file_shape)
        tasks[key] = (_load_batch, loaders)

    dsk = dask.highlevelgraph.HighLevelGraph.from_collections("load_files", tasks, dependencies=())
    chunks = (tuple(len(b) for b in batches),) + tuple((s,) for s in file_shape)
    array = dask.array.Array(dsk,
                             name="load_files",
                             chunks=chunks,
                             dtype=loader_array.flat[0].dtype)
    return array


def _load_batch(loaders):
    arrays = [loader.data for loader in loaders]
    if len(arrays) == 1:
        return arrays[0]
    return np.concatenate(arrays)
