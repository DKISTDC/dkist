from pathlib import Path

import numpy as np

from asdf.tags.core.external_reference import ExternalArrayReference
from astropy.wcs.wcsapi.wrappers.sliced_wcs import sanitize_slices

from dkist.io.dask_utils import stack_loader_array
from dkist.net import conf as net_conf
from dkist.net.globus.transfer import _orchestrate_transfer_task

__all__ = ['SlicedFileManagerProxy', 'FileManager']


class SlicedFileManagerProxy:
    """
    A sliced view into a `.FileManager` object.
    """
    __slots__ = ["parent", "parent_slice"]

    def __init__(self, file_manager, aslice):
        self.parent = file_manager
        self.parent_slice = tuple(aslice)

    def __getattr__(self, name):
        """
        Proxy all attributes to the parent object if they aren't found on this object.
        """
        return getattr(self.parent, name)

    def __setattr__(self, name, value):
        if name not in self.__slots__:
            return self.parent.__setattr__(name, value)

        return super().__setattr__(name, value)

    def __len__(self):
        return self._reference_array.size

    @property
    def _loader_array(self):
        """
        An array of `.BaseFITSLoader` objects.
        """
        la = self.parent._loader_array
        return np.array(la[self.parent_slice])

    @property
    def _reference_array(self):
        """
        An array of `asdf.ExternalArrayReference` objects.
        """
        ra = self.parent._reference_array
        return np.array(ra[self.parent_slice])

    @property
    def output_shape(self):
        # If the first dimension is one we are going to squash it.
        shape = self.parent.shape
        if self.shape[0] == 1:
            shape = self.parent.shape[1:]

        if len(self._reference_array) == 1:
            return shape
        else:
            return tuple(list(self._reference_array.shape) + list(shape))


class BaseFileManager:
    """
    Manage a collection of arrays in files and their conversion to a Dask Array.
    """

    def __init__(self, fileuris, target, dtype, shape, *, loader, basepath=None):
        shape = tuple(shape)
        self.shape = shape
        self.dtype = dtype
        self.target = target
        self._loader = loader
        self._basepath = None
        self.__reference_array = np.asarray(self._to_ears(fileuris), dtype=object)
        # When this object is attached to a Dataset object this attribute will
        # be populated with a reference to that Dataset instance.
        self._ndcube = None

        # Use the setter to convert to a Path
        self.basepath = Path(basepath) if basepath is not None else None

        loader_array = np.empty_like(self._reference_array, dtype=object)
        for i, ele in enumerate(self._reference_array.flat):
            loader_array.flat[i] = loader(ele, self)

        self.__loader_array = loader_array

    def __len__(self):
        return self._reference_array.size

    def __eq__(self, other):
        uri = self.filenames == other.filenames
        target = self.target == other.target
        dtype = self.dtype == other.dtype
        shape = self.shape == other.shape

        return all((uri, target, dtype, shape))

    def __getitem__(self, item):
        item = sanitize_slices(item, self._reference_array.ndim)
        return SlicedFileManagerProxy(self, item)

    def _array_slice_to_reference_slice(self, aslice):
        """
        Convert a slice for the reconstructed array to a slice for the reference_array.
        """
        shape = self.shape
        aslice = list(sanitize_slices(aslice, len(self.output_shape)))
        if shape[0] == 1:
            # Insert a blank slice for the removed dimension
            aslice.insert(len(shape) - 1, slice(None))
        aslice = aslice[len(shape):]
        return tuple(aslice)

    def _slice_by_cube(self, item):
        item = self._array_slice_to_reference_slice(item)

        # Apply slice as array, but then back to nested lists
        uris = np.array(self._fileuris)[item].tolist()
        if isinstance(uris, str):
            uris = [uris]

        return type(self)(uris, self.target, self.dtype, self.shape,
                          loader=self._loader, basepath=self.basepath)

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
        return self._reference_array.tolist()

    @property
    def basepath(self):
        """
        The path all arrays generated from this ``FileManager`` use to read data from.
        """
        return self._basepath

    @basepath.setter
    def basepath(self, value):
        self._basepath = Path(value).expanduser() if value is not None else None

    @property
    def _loader_array(self):
        """
        An array of `.BaseFITSLoader` objects.

        These loader objects implement the minimal array-like interface for
        conversion to a dask array.
        """
        return self.__loader_array

    @property
    def _reference_array(self):
        """
        An array of `asdf.ExternalArrayReference` objects.
        """
        return self.__reference_array

    @property
    def filenames(self):
        """
        Return a list of file names referenced by this Array Container.
        """
        names = []
        for ear in self._reference_array.flat:
            names.append(ear.fileuri)
        return names

    @property
    def _fileuris(self):
        """
        Nested lists of filenames.

        Note: this is not a flat list unlike `self.filenames`
        """
        return np.array(self.filenames).reshape(self._loader_array.shape).tolist()

    @property
    def output_shape(self):
        """
        The final shape of the reconstructed data array.
        """
        # If the first dimension is one we are going to squash it.
        shape = self.shape
        if self.shape[0] == 1:
            shape = self.shape[1:]

        if len(self._reference_array) == 1:
            return shape
        else:
            return tuple(list(self._reference_array.shape) + list(shape))

    def _generate_array(self):
        """
        Construct a `dask.array.Array` object from this set of references.

        Each call to this method generates a new array, but all the loaders
        still have a reference to this `~.FileManager` object, meaning changes
        to this object will be reflected in the data loaded by the array.
        """
        return stack_loader_array(self._loader_array).reshape(self.output_shape)


class FileManager(BaseFileManager):
    """
    Manage the collection of FITS files backing a `~dkist.Dataset`.

    Each `~dkist.Dataset` object is backed by a number of FITS files, each holding a
    slice of the total array. This class provides tools for inspecting and
    retrieving these FITS files, as well as specifying where to load these
    files from.
    """
    def download(self, path=None, destination_endpoint=None, progress=True, wait=True):
        """
        Start a Globus file transfer for all files in this Dataset.

        Parameters
        ----------
        path : `pathlib.Path` or `str`, optional
            The path to save the data in, must be accessible by the Globus
            endpoint.
            The default value is ``.basepath``, if this is None it will default
            to ``/~/``.
            It is possible to put placeholder strings in the path with any key
            from the dataset inventory dictionary which can be accessed as
            ``ds.meta['inventory']``. An example of this would be
            ``path="~/dkist/{datasetId}"`` to save the files in a folder named
            with the dataset ID being downloaded.

        destination_endpoint : `str`, optional
            A unique specifier for a Globus endpoint. If `None` a local
            endpoint will be used if it can be found, otherwise an error will
            be raised. See `~dkist.net.globus.get_endpoint_id` for valid
            endpoint specifiers.

        progress : `bool` or `str`, optional
           If `True` status information and a progress bar will be displayed
           while waiting for the transfer to complete.
           If ``progress="verbose"`` then all globus events generated during
           the transfer will be shown (by default only error messages are
           shown.)

        wait : `bool`, optional
            If `False` then the function will return while the Globus transfer task
            is still running. Setting ``wait=False`` implies ``progress=False``.
        """
        if self._ndcube is None:
            raise ValueError(
                "This file manager has no associated Dataset object, so the data can not be downloaded."
            )

        inv = self._ndcube.meta["inventory"]

        base_path = Path(net_conf.dataset_path.format(**inv))
        destination_path = path or self.basepath or "/~/"
        destination_path = Path(destination_path).as_posix()
        destination_path = Path(destination_path.format(**inv))

        # TODO: If we are transferring the whole dataset then we should use the
        # directory not the list of all the files in it.
        file_list = [base_path / fn for fn in self.filenames]
        file_list.append(Path("/") / inv['bucket'] / inv['asdfObjectKey'])
        file_list.append(Path("/") / inv['bucket'] / inv['browseMovieObjectKey'])
        file_list.append(Path("/") / inv['bucket'] / inv['qualityReportObjectKey'])

        # TODO: Ascertain if the destination path is local better than this
        is_local = not destination_endpoint

        _orchestrate_transfer_task(file_list,
                                   recursive=False,
                                   destination_path=destination_path,
                                   destination_endpoint=destination_endpoint,
                                   progress=progress,
                                   wait=wait)

        if is_local:
            local_destination = destination_path.relative_to("/").expanduser()
            if local_destination.root == "":
                local_destination = "/" / local_destination
            self.basepath = local_destination
