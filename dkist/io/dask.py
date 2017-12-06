"""
This file takes the lazy FITS loader classes and returns a dask array from them.
"""
import abc
from functools import partial

import numpy as np
import dask.array as da
from asdf.tags.core.external_reference import ExternalArrayReference


__all__ = ['BaseFITSArrayContainer', 'NumpyFITSArrayContainer', 'DaskFITSArrayContainer']


class BaseFITSArrayContainer(metaclass=abc.ABCMeta):
    """
    Given an array of `~dkist.io.fits.BaseFITSLoader` instances construct a
    contiguous array type from them.
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

    def __array__(self):
        return self.array


class NumpyFITSArrayContainer(BaseFITSArrayContainer):
    """
    Load it ALL INTO RAM.
    """

    @property
    def array(self):
        aa = map(np.asarray, self.reference_array.flat)
        return np.stack(aa, axis=0).reshape(self.shape)


class DaskFITSArrayContainer(BaseFITSArrayContainer):
    """
    Do not load it all into RAM.
    """

    @property
    def array(self):
        chunk = tuple(self.loader_array.flat[0].shape)
        aa = map(
            partial(da.from_array, chunks=chunk), self.loader_array.flat)
        return da.stack(list(aa)).reshape(self.shape)
