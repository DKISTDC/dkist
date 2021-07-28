import os
from typing import Any
from pathlib import Path

import numpy as np

from dkist.io.array_containers import BaseFITSArrayCollection

try:
    from numpy.typing import ArrayLike
except ImportError:
    ArrayLike = Any


class FileManager:
    """
    Manages the set of files which back a DKIST `~.Dataset`.
    """

    def __init__(self, array_collection, file_slice=None):
        self._array_collection = array_collection
        self._file_slice = None

    @property
    def data(self) -> ArrayLike:
        """
        The array object generated from the files.
        """
        return self.array_collection.get_array(self._file_slice)

    @property
    def array_collection(self) -> BaseFITSArrayCollection:
        """
        The `~.BaseFITSArrayCollection object which loads arrays from the files.
        """
        return self._array_collection

    @property
    def base_path(self) -> os.PathLike:
        """
        Root path for all the FITS files.
        """
        return self.array_collection.loader.keywords["base_path"]

    @base_path.setter
    def base_path(self, base_path: os.PathLike):
        """
        Set the base path.

        This triggers a rebuild in the array collection.
        """
        kwargs = self.array_collection.loader.keywords.copy()
        kwargs["base_path"] = Path(base_path)
        self.array_collection.set_loader_kwargs(**kwargs)

    def __getitem__(self, item):
        return type(self)(self.array_collection, item)

    # def sliced_output_shape(self, aslice):
    #     return np.broadcast_to(1, self.output_shape)[aslice].shape

    # def array_slice_to_reference_slice(self, aslice):
    #     """
    #     Convert a slice for the reconstructed array to a slice fort the reference_array.
    #     """
    #     aslice = list(sanitize_slices(aslice, len(self.output_shape)))
    #     if self.shape[0] == 1:
    #         # Insert a blank slice for the removed dimension
    #         aslice.insert(len(self.shape) - 1, slice(None))
    #     aslice = aslice[len(self.shape):]
    #     return tuple(aslice)
