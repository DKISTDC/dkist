"""
This submodule provides tools for resolving arrays of
`asdf.ExternalArrayReference` objects to Python array-like objects.
"""
import abc
from functools import partial

import numpy as np
import dask.array as da
from sunpy.util.decorators import add_common_docstring
from asdf.tags.core.external_reference import ExternalArrayReference


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

        reference_shape = reference_array.flat[0].shape

        self.shape = tuple(list(reference_array.shape) + list(reference_shape))

        loader_array = np.empty_like(reference_array, dtype=object)
        for i, ele in enumerate(reference_array.flat):
            loader_array.flat[i] = loader(ele, **kwargs)
        self.loader_array = loader_array

    def _check_contents(self, reference_array):
        """
        Validate that the array re fence objects are compatible with each other,
        i.e. same dimensions and same dtype.
        """
        shape = reference_array.flat[0].shape
        dtype = reference_array.flat[0].dtype
        for i, ele in enumerate(reference_array.flat):
            # TODO: Make these not asserts
            assert isinstance(ele, ExternalArrayReference)
            assert ele.dtype == dtype
            assert ele.shape == shape

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
        chunk = tuple(self.loader_array.flat[0].shape)
        aa = map(
            partial(da.from_array, chunks=chunk), self.loader_array.flat)
        return da.stack(list(aa)).reshape(self.shape)
