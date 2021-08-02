from pathlib import Path

import numpy as np

from asdf.tags.core.external_reference import ExternalArrayReference

from dkist.io.dask_utils import stack_loader_array
from dkist.io.loaders import AstropyFITSLoader


class FileManager:
    """
    Manage a collection of arrays in files and their conversion to a Dask Array.
    """

    @classmethod
    def from_tree(cls, node, ctx):
        filepath = Path((ctx.uri or ".").replace("file:", ""))
        base_path = filepath.parent

        file_manager = cls(node['fileuris'],
                           node['target'],
                           node['datatype'],
                           node['shape'],
                           loader=AstropyFITSLoader,
                           basepath=base_path)
        return file_manager

    @classmethod
    def to_tree(cls, data, ctx):
        node = {}
        node['fileuris'] = data.fileuris
        node['target'] = data.target
        node['datatype'] = data.dtype
        node['shape'] = data.shape
        return node

    def __init__(self, fileuris, target, dtype, shape, *, loader, basepath=None):
        shape = tuple(shape)
        self.shape = shape
        self.dtype = dtype
        self.target = target
        self.fileuris = fileuris
        self._loader = loader
        self._basepath = None
        self._reference_array = np.asarray(self.external_array_references, dtype=object)
        # Use the setter to convert to a Path
        self.basepath = basepath

        # If the first dimension is one we are going to squash it.
        if shape[0] == 1:
            shape = shape[1:]
        if len(self._reference_array) == 1:
            self.output_shape = shape
        else:
            self.output_shape = tuple(list(self._reference_array.shape) + list(shape))

        loader_array = np.empty_like(self._reference_array, dtype=object)
        for i, ele in enumerate(self._reference_array.flat):
            loader_array.flat[i] = loader(ele, self)

        self.loader_array = loader_array

    def __len__(self):
        return self._reference_array.size

    def __eq__(self, other):
        uri = self.fileuris == other.fileuris
        target = self.target == other.target
        dtype = self.dtype == other.dtype
        shape = self.shape == other.shape

        return all((uri, target, dtype, shape))

    def __getitem__(self, item):
        # Apply slice as array, but then back to nested lists
        uris = np.array(self.fileuris)[item].tolist()
        if isinstance(uris, str):
            uris = [uris]
        # Override this method to set loader
        return type(self)(uris, self.target, self.dtype, self.shape, loader=self._loader)

    def _to_ears(self, urilist):
        # This is separate to the property because it's recursive
        if isinstance(urilist, (list, tuple)):
            return list(map(self._to_ears, urilist))
        return ExternalArrayReference(urilist, self.target, self.dtype, self.shape)

    @property
    def external_array_references(self):
        """
        Represent this collection as a list of `asdf.ExternalArrayReference` objects.
        """
        return self._to_ears(self.fileuris)

    @property
    def basepath(self):
        """
        The path all arrays generated from this ``FileManager`` use to read data from.
        """
        return self._basepath

    @basepath.setter
    def basepath(self, value):
        self._basepath = Path(value) if value is not None else None

    @property
    def filenames(self):
        """
        Return a list of file names referenced by this Array Container.
        """
        names = []
        for furi in np.asarray(self.fileuris).flat:
            names.append(furi)
        return names

    def generate_array(self):
        """
        The `~dask.array.Array` associated with this array of references.
        """
        return stack_loader_array(self.loader_array).reshape(self.output_shape)

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

        # TODO: This is a hack to change the base dir of the dataset.
        # The real solution to this is to use the database.
        local_destination = destination_path.relative_to("/").expanduser()
        old_ac = self._array_container
        self._array_container = FileManager.from_external_array_references(
            old_ac.external_array_references,
            loader=old_ac._loader,
            basepath=local_destination)
        self._data = self._array_container.array
