"""
This submodule provides tools for resolving arrays of
`asdf.ExternalArrayReference` objects to Python array-like objects.
"""
import abc
from functools import partial

import dask.array as da
import numpy as np

from asdf.tags.core.external_reference import ExternalArrayReference
from sunpy.util.decorators import add_common_docstring

__all__ = ['BaseFITSArrayContainer', 'NumpyFITSArrayContainer', 'DaskFITSArrayContainer']

common_parameters = """

    Parameters
    ----------

    reference_array : `~numpy.ndarray` or `list`
        A (multi-dimensional) array of `asdf.ExternalArrayReference` objects.

    loader : `dkist.io.fits.BaseFITSLoader`
        The loader subclass to use to resolve each `~asdf.ExternalArrayReference`.

    kwargs : `dict`
        Extra keyword arguments are passed to the loader class.
"""


@add_common_docstring(append=common_parameters)
class BaseFITSArrayContainer(metaclass=abc.ABCMeta):
    """
    This class provides an array-like interface to an array of
    `asdf.ExternalArrayReference` objects.
    """

    def __init__(self, reference_array, *, loader, **kwargs):
        reference_array = np.asarray(reference_array, dtype=object)
        self._check_contents(reference_array)

        # If the first dimension is one we are going to squash it.
        reference_shape = reference_array.flat[0].shape
        if reference_shape[0] == 1:
            reference_shape = reference_shape[1:]

        if len(reference_array) == 1:
            self.shape = reference_shape
        else:
            self.shape = tuple(list(reference_array.shape) + list(reference_shape))

        loader_array = np.empty_like(reference_array, dtype=object)
        for i, ele in enumerate(reference_array.flat):
            loader_array.flat[i] = loader(ele, **kwargs)

        self.loader_array = loader_array
        self._loader = partial(loader, **kwargs)
        self.reference_array = reference_array

    def _check_contents(self, reference_array):
        """
        Validate that the array reference objects are compatible with each other,
        i.e. same dimensions and same dtype.
        """
        shape = reference_array.flat[0].shape
        dtype = reference_array.flat[0].dtype
        for i, ele in enumerate(reference_array.flat):
            # TODO: Make these not asserts
            assert isinstance(ele, ExternalArrayReference)
            assert ele.dtype == dtype
            assert ele.shape == shape

    def __getitem__(self, item):
        return type(self)(self.reference_array[item], loader=self._loader)

    def as_external_array_references(self):
        """
        Convert the loader array back to a nested list of
        `asdf.ExternalArrayReference` objects.
        """
        ears = np.empty_like(self.loader_array)
        for i, lelem in enumerate(self.loader_array.flat):
            ears.flat[i] = lelem.fitsarray
        return ears.tolist()

    @property
    def filenames(self):
        """
        Return a list of file names referenced by this Array Container.
        """
        names = []
        for ear in self.reference_array.flat:
            names.append(ear.fileuri)
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
        return np.stack(aa, axis=0).reshape(self.shape)


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
        return stack_loader_array(self.loader_array).reshape(self.shape)


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
