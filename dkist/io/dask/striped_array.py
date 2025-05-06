"""
This module contains two key classes:

* ``StripedExternalArray``: The object which tracks the ``BaseFITSLoader``
  objects and the file references and their shape, and constructs a Dask Array.
  The loader object (which actually reads the data out of the FITS files) holds
  a reference back to this object which it uses to resolve the file paths at
  load time.
* ``FileManager``: The object providing the public API, which can be sliced.

The slicing functionality on the ``FileManager`` object works by constructing a
view into the original ``StripedExternalArray`` object through the
``StripedExternalArrayView`` class.
"""
import os
import abc
from typing import Any
from pathlib import Path
from collections.abc import Iterable

import dask.array
import numpy as np
from numpy.typing import DTypeLike, NDArray

from astropy.wcs.wcsapi.wrappers.sliced_wcs import sanitize_slices

from dkist.io.dask.loaders import BaseFITSLoader
from dkist.io.dask.utils import stack_loader_array

__all__ = ["FileManager", "StripedExternalArray"]


class BaseStripedExternalArray(abc.ABC):
    """
    Implements shared functionality between FITSLoader and FITSLoaderView.
    """
    target: Any
    dtype: DTypeLike
    shape: Iterable[int]
    chunksize: Iterable[int] | None

    @abc.abstractproperty
    def fileuri_array(self) -> NDArray[np.str_]:
        """
        An array of relative (to ``basepath``) file uris.
        """

    # np.object_ isn't a generic so we can't type hint the actual type
    # https://github.com/numpy/numpy/issues/25351
    @abc.abstractproperty
    def loader_array(self) -> NDArray[np.object_]:
        """
        An array of `.BaseFITSLoader` objects.

        These loader objects implement the minimal array-like interface for
        conversion to a dask array.
        """

    def __len__(self) -> int:
        return self.loader_array.size

    def __eq__(self, other) -> bool:
        uri = (self.fileuri_array == other.fileuri_array).all()
        target = self.target == other.target
        dtype = self.dtype == other.dtype
        shape = self.shape == other.shape

        return all((uri, target, dtype, shape))

    @staticmethod
    def _output_shape_from_ref_array(shape, loader_array) -> tuple[int]:
        # If the first dimension is one we are going to squash it.
        if shape[0] == 1:
            shape = shape[1:]

        if loader_array.size == 1:
            return shape

        return tuple(list(loader_array.shape) + list(shape))

    @property
    def output_shape(self) -> tuple[int, ...]:
        """
        The final shape of the reconstructed data array.
        """
        return self._output_shape_from_ref_array(self.shape, self.loader_array)

    def _generate_array(self) -> dask.array.Array:
        """
        Construct a `dask.array.Array` object from this set of references.

        Each call to this method generates a new array, but all the loaders
        still have a reference to this `~.FileManager` object, meaning changes
        to this object will be reflected in the data loaded by the array.
        """
        return stack_loader_array(self.loader_array, self.chunksize).reshape(self.output_shape)


class StripedExternalArray(BaseStripedExternalArray):
    def __init__(
        self,
        fileuris: Iterable[str],
        target: Any,
        dtype: DTypeLike,
        shape: Iterable[int],
        *,
        loader: type[BaseFITSLoader],
        basepath: os.PathLike = None,
        chunksize: Iterable[int] = None,
    ):
        shape = tuple(shape)
        self.shape = shape
        self.dtype = dtype
        self.target = target
        self._loader = loader
        self._basepath = self._sanitize_basepath(basepath)
        self.chunksize = chunksize
        self._fileuri_array = np.atleast_1d(np.array(fileuris))

        loader_array = np.empty_like(self._fileuri_array, dtype=object)
        for i, fileuri in enumerate(self._fileuri_array.flat):
            loader_array.flat[i] = loader(fileuri, shape, dtype, target, self.basepath)

        self._loader_array = loader_array

    def __str__(self) -> str:
        return f"FITSLoader {len(self)} files with shape {self.shape}"

    def __repr__(self) -> str:
        return f"{object.__repr__(self)}\n{self}"

    @property
    def ndim(self):
        return len(self.loader_array.shape)

    @staticmethod
    def _sanitize_basepath(value):
        return Path(value).expanduser() if value is not None else None

    @property
    def basepath(self) -> os.PathLike:
        """
        The path all arrays generated from this ``FileManager`` use to read data from.
        """
        return self._basepath

    @basepath.setter
    def basepath(self, value: os.PathLike | str | None):
        self._basepath = self._sanitize_basepath(value)
        for loader in self._loader_array.flat:
            loader.basepath = self._basepath

    @property
    def fileuri_array(self) -> NDArray[np.str_]:
        """
        An array of relative (to ``basepath``) file uris.
        """
        return self._fileuri_array

    @property
    def loader_array(self) -> NDArray[np.object_]:
        """
        An array of `.BaseFITSLoader` objects.

        These loader objects implement the minimal array-like interface for
        conversion to a dask array.
        """
        return self._loader_array


class StripedExternalArrayView(BaseStripedExternalArray):
    # This class presents a view int a FITSLoader object It applies a slice to
    # the fileuri_array and loader_array properties Any property which
    # references the sliced objects should be defined in Base or this view
    # class.
    __slots__ = ["parent", "parent_slice"]

    def __init__(self, parent: StripedExternalArray, aslice: tuple | slice | int):
        self.parent = parent
        self.parent_slice = tuple(aslice) if isinstance(aslice, (tuple, list)) else (aslice,)

    def __getattr__(self, attr):
        return getattr(self.parent, attr)

    def __str__(self):
        return f"FITSLoader View <{self.parent_slice}> into {self.parent}"

    def __repr__(self):
        return f"{object.__repr__(self)}\n{self}"

    @property
    def basepath(self) -> os.PathLike:
        """
        The path all arrays generated from this ``FileManager`` use to read data from.
        """
        return self.parent.basepath

    @basepath.setter
    def basepath(self, value):
        self.parent.basepath = value

    @property
    def fileuri_array(self) -> NDArray[np.str_]:
        """
        An array of relative (to ``basepath``) file uris.
        """
        # array call here to ensure that a length one array is returned rather
        # than a single element.
        return np.array(self._fileuri_array[self.parent_slice])

    @property
    def loader_array(self) -> NDArray[np.object_]:
        """
        An array of `.BaseParent` objects.

        These loader objects implement the minimal array-like interface for
        conversion to a dask array.
        """
        # array call here to ensure that a length one array is returned rather
        # than a single element.
        return np.array(self._loader_array[self.parent_slice])


class FileManager:
    """
    A class for managing the files which create a striped Dask array from a group of files.

    Parameters
    ----------
    striped_external_array
    """
    __slots__ = ["_striped_external_array"]

    @classmethod
    def from_parts(cls, fileuris, target, dtype, shape, *, loader, basepath=None, chunksize=None):
        """
        An initialization helper for constructing the `StripedExternalArray` and the `FileManager` together.
        """
        striped_array = StripedExternalArray(
            fileuris, target, dtype, shape, loader=loader, basepath=basepath, chunksize=None,
        )
        return cls(striped_array)

    def __init__(self, striped_external_array: StripedExternalArray):
        self._striped_external_array = striped_external_array

    def __eq__(self, other):
        return self._striped_external_array == other._striped_external_array

    def __len__(self):
        return len(self._striped_external_array)

    def __str__(self) -> str:
        return f"FileManager containing {len(self)} files with each array having shape {self.shape}"

    def __repr__(self) -> str:
        return f"{object.__repr__(self)}\n{self}"

    def __getitem__(self, item):
        item = sanitize_slices(item, self._striped_external_array.ndim)
        return type(self)(StripedExternalArrayView(self._striped_external_array, item))

    def _array_slice_to_loader_slice(self, aslice):
        """
        Convert a slice for the reconstructed array to a slice for the loader_array.
        """
        fits_array_shape = self._striped_external_array.shape
        aslice = list(sanitize_slices(aslice, len(self.output_shape)))
        if fits_array_shape[0] == 1:
            # Insert a blank slice for the dummy dimension
            aslice.insert(-(len(fits_array_shape)-1), slice(None))
        # Now only use the dimensions of the slice not covered by the array axes
        aslice = aslice[:-1*len(fits_array_shape)]
        return tuple(aslice)

    def _slice_by_cube(self, item):
        item = self._array_slice_to_loader_slice(item)
        loader_view = StripedExternalArrayView(self._striped_external_array, item)
        return type(self)(loader_view)

    def _generate_array(self):
        return self._striped_external_array._generate_array()

    # @cached_property
    @property
    def dask_array(self):
        """
        The Dask array managed by this FileManager.

        .. note::
           This array is cached, so only generated once.

        """
        return self._generate_array()

    @property
    def fileuri_array(self):
        """
        An array of all the fileuris referenced by this `.FileManager`.

        This array is shaped to match the striped dimensions of the dataset.
        """
        return self._striped_external_array.fileuri_array

    @property
    def basepath(self):
        """
        The path all arrays generated from this ``FileManager`` use to read data from.
        """
        return self._striped_external_array.basepath

    @basepath.setter
    def basepath(self, value):
        self._striped_external_array.basepath = value

    @property
    def filenames(self):
        """
        Return a list of file names referenced by this Array Container.
        """
        return self.fileuri_array.flatten().tolist()

    @property
    def output_shape(self):
        """
        The shape of the generated Dask array.
        """
        return self._striped_external_array.output_shape

    @property
    def shape(self):
        """
        Shape of the file reference array.

        This is not the shape of the output array, it's the shape of the files
        which need to be loaded to generate that output array.
        """
        return self._striped_external_array.shape
