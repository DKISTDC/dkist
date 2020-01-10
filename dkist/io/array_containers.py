"""
This submodule provides tools for resolving arrays of
`asdf.ExternalArrayReference` objects to Python array-like objects.
"""
import abc
import collections
from functools import partial

import dask.array as da
import numpy as np

from asdf.tags.core.external_reference import ExternalArrayReference, ExternalArrayReferenceCollection
from sunpy.util.decorators import add_common_docstring

__all__ = ['BaseFITSArrayContainer', 'NumpyFITSArrayContainer', 'DaskFITSArrayContainer']


common_parameters = """

    Parameters
    ----------

    fileuris: `list` or `tuple`
        An interable of paths to be referenced. Can be nested arbitarily deep.

    target: `object`
        Some internal target to the data in the files. Examples may include a HDU
        index, a HDF path or an asdf fragment.

    dtype: `str`
        The (numpy) dtype of the contained arrays.

    shape: `tuple`
        The shape of the arrays to be loaded.

    loader : `dkist.io.BaseFITSLoader`
        The loader subclass to use to resolve each `~asdf.ExternalArrayReference`.

    kwargs : `dict`
        Extra keyword arguments are passed to the loader class.
"""

@add_common_docstring(append=common_parameters)
class BaseFITSArrayContainer(ExternalArrayReferenceCollection):
    """
    A collection of references to homogenous FITS arrays.
    """
    name = "array_container"
    organization = "dkist.nso.edu"
    requires = ['dkist']
    version = "0.2.0"
    yaml_tag = "dkist.nso.edu:dkist/array_container-0.2.0"

    @classmethod
    def from_tree(cls, node, ctx):
        # TODO: Work out a way over overriding this at dataset load.
        filepath = Path((ctx.uri or ".").replace("file:", ""))
        base_path = filepath.parent

        # TODO: The choice of Dask and Astropy here should be in a config somewhere.
        array_container = DaskFITSArrayContainer(node['fileuris'],
                                                 node['target'],
                                                 node['dtype'],
                                                 node['shape'],
                                                 loader=AstropyFITSLoader,
                                                 basepath=base_path)
        return array_container


    def __init__(self, fileuris, target, dtype, shape, *, loader, **kwargs):
        super().__init__(fileuris, target, dtype, shape)
        reference_array = np.asarray(self.external_array_references, dtype=object)

        # If the first dimension is one we are going to squash it.
        reference_shape = self.shape
        if reference_shape[0] == 1:
            reference_shape = reference_shape[1:]
        if len(reference_array) == 1:
            self.output_shape = reference_shape
        else:
            self.output_shape = tuple(list(reference_array.shape) + list(reference_shape))

        loader_array = np.empty_like(reference_array, dtype=object)
        for i, ele in enumerate(reference_array.flat):
            loader_array.flat[i] = loader(ele, **kwargs)

        self.loader_array = loader_array
        self._loader = partial(loader, **kwargs)

    def __getitem__(self, item):
        return type(self)(self.reference_array[item], loader=self._loader)

    @property
    def filenames(self):
        """
        Return a list of file names referenced by this Array Container.
        """
        names = []
        for furi in np.asarray(self.fileuris).flat:
            names.append(furi)
        return names

    @abc.abstractproperty
    def array(self):
        """
        Return an array type for the given array of external file references.
        """


@add_common_docstring(append=common_parameters)
class NumpyFITSArrayContainer(BaseFITSArrayContainer):
    """
    Load an array of `~asdf.ExternalArrayReference` objects into a single
    in-memory numpy array.
    """

    def __array__(self):
        """
        This dosen't seem to work if it returns a Dask array, so it's only
        useful here.
        """
        return self.array

    @property
    def array(self):
        """
        The `~numpy.ndarray` associated with this array of references.
        """
        aa = map(np.asarray, self.loader_array.flat)
        return np.stack(aa, axis=0).reshape(self.output_shape)


@add_common_docstring(append=common_parameters)
class DaskFITSArrayContainer(BaseFITSArrayContainer):
    """
    Load an array of `~asdf.ExternalArrayReference` objects into a
    `dask.array.Array` object.
    """

    @property
    def array(self):
        """
        The `~dask.array.Array` associated with this array of references.
        """
        return stack_loader_array(self.loader_array).reshape(self.output_shape)


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
