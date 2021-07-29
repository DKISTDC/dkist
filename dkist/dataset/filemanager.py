import os
from typing import Any
from pathlib import Path

import numpy as np

from astropy.wcs.wcsapi.wrappers.sliced_wcs import sanitize_slices, combine_slices

from dkist.io.array_collections import BaseFITSArrayCollection
from dkist.utils.globus import (DKIST_DATA_CENTRE_DATASET_PATH, DKIST_DATA_CENTRE_ENDPOINT_ID,
                                start_transfer_from_file_list, watch_transfer_progress)
from dkist.utils.globus.endpoints import get_local_endpoint_id, get_transfer_client

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

    @property
    def filenames(self):
        return self.array_collection.get_filenames(self._file_slice)

    def __getitem__(self, item):
        item = sanitize_slices(item, self.array_collection.reference_array.ndim)
        if self._file_slice is not None:
            item = tuple(combine_slices(s1, s2) for s1, s2 in zip(item, self._file_slice))
        return type(self)(self.array_collection, item)

    def _get_array_item(self, item):
        return self[self.array_slice_to_reference_slice(item)]

    def array_slice_to_reference_slice(self, aslice):
        """
        Convert a slice for the reconstructed array to a slice fort the reference_array.
        """
        output_shape = self.array_collection.get_output_shape(self._file_slice)
        shape = self.array_collection.shape
        aslice = list(sanitize_slices(aslice, len(output_shape)))
        if shape[0] == 1:
            # Insert a blank slice for the removed dimension
            aslice.insert(len(shape) - 1, slice(None))
        aslice = aslice[len(shape):]
        return tuple(aslice)

    def download(self, path="/~/", destination_endpoint=None, progress=True):
        """
        Start a Globus file transfer for all files in this Dataset.

        Parameters
        ----------
        path : `pathlib.Path` or `str`, optional
            The path to save the data in, must be accessible by the Globus
            endpoint.

        destination_endpoint : `str`, optional
            A unique specifier for a Globus endpoint. If `None` a local
            endpoint will be used if it can be found, otherwise an error will
            be raised. See `~dkist.utils.globus.get_endpoint_id` for valid
            endpoint specifiers.

        progress : `bool`, optional
           If `True` status information and a progress bar will be displayed
           while waiting for the transfer to complete.
        """

        base_path = Path(DKIST_DATA_CENTRE_DATASET_PATH.format(**self.meta))
        # TODO: Default path to the config file
        destination_path = Path(path) / self.meta['primaryProposalId'] / self.meta['datasetId']

        file_list = [base_path / fn for fn in self.filenames]
        file_list.append(Path("/") / self.meta['bucket'] / self.meta['asdfObjectKey'])

        if not destination_endpoint:
            destination_endpoint = get_local_endpoint_id()

        task_id = start_transfer_from_file_list(DKIST_DATA_CENTRE_ENDPOINT_ID,
                                                destination_endpoint, destination_path,
                                                file_list)

        tc = get_transfer_client()
        if progress:
            watch_transfer_progress(task_id, tc, initial_n=len(file_list))
        else:
            tc.task_wait(task_id, timeout=1e6)

        # TODO: Work out if the destination is actually local or not.
        local_destination = destination_path.relative_to("/").expanduser()
        self.base_path = local_destination

