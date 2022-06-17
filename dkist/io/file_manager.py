from pathlib import Path

import numpy as np

from asdf.tags.core.external_reference import ExternalArrayReference
from astropy.wcs.wcsapi.wrappers.sliced_wcs import sanitize_slices

from dkist.io.dask_utils import stack_loader_array
from dkist.net.helpers import _orchestrate_transfer_task
from dkist.net import conf as net_conf


class FITSLoader:
    def __init__(self, fileuris, target, dtype, shape, *, loader, basepath=None):
        shape = tuple(shape)
        self.shape = shape
        self.dtype = dtype
        self.target = target
        self._loader = loader
        self._basepath = None
        self.basepath = basepath  # Use the setter to convert to a Path

        self._reference_array = np.asarray(self._to_ears(fileuris), dtype=object)

        loader_array = np.empty_like(self.reference_array, dtype=object)
        for i, ele in enumerate(self.reference_array.flat):
            loader_array.flat[i] = loader(ele, self)

        self._loader_array = loader_array

    def __len__(self):
        return self.reference_array.size

    def __eq__(self, other):
        uri = (self.reference_array == other.reference_array).all()
        target = self.target == other.target
        dtype = self.dtype == other.dtype
        shape = self.shape == other.shape

        return all((uri, target, dtype, shape))

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
    def reference_array(self):
        """
        An array of `asdf.ExternalArrayReference` objects.
        """
        return self._reference_array

    @property
    def loader_array(self):
        """
        An array of `.BaseFITSLoader` objects.

        These loader objects implement the minimal array-like interface for
        conversion to a dask array.
        """
        return self._loader_array

    @staticmethod
    def _output_shape_from_ref_array(shape, reference_array):
        # If the first dimension is one we are going to squash it.
        if shape[0] == 1:
            shape = shape[1:]

        if len(reference_array) == 1:
            return shape
        else:
            return tuple(list(reference_array.shape) + list(shape))

    @property
    def output_shape(self):
        """
        The final shape of the reconstructed data array.
        """
        return self._output_shape_from_ref_array(self.shape, self.reference_array)

    @property
    def _fileuris(self):
        """
        Numpy array of fileuris
        """
        return np.vectorize(lambda x: x.fileuri)(self.reference_array)

    def _to_ears(self, urilist):
        # This is separate to the property because it's recursive
        if isinstance(urilist, (list, tuple)):
            return list(map(self._to_ears, urilist))
        return ExternalArrayReference(urilist, self.target, self.dtype, self.shape)

    def _generate_array(self):
        """
        Construct a `dask.array.Array` object from this set of references.

        Each call to this method generates a new array, but all the loaders
        still have a reference to this `~.FileManager` object, meaning changes
        to this object will be reflected in the data loaded by the array.
        """
        return stack_loader_array(self.loader_array).reshape(self.output_shape)


class FITSLoaderView:
    __slots__ = ["parent", "parent_slice"]

    def __init__(self, parent, aslice):
        self.parent = parent
        self.parent_slice = tuple(aslice)

    def __getattr__(self, attr):
        return getattr(self.parent, attr)

    def __len__(self):
        return self.reference_array.size

    def __str__(self):
        return f"FITSLoader View <{self.parent_slice}> into {self.parent}"

    def __repr__(self):
        return f"{object.__repr__(self)}\n{self}"

    @property
    def basepath(self):
        """
        The path all arrays generated from this ``FileManager`` use to read data from.
        """
        return self.parent.basepath

    @basepath.setter
    def basepath(self, value):
        self.parent.basepath = value

    @property
    def reference_array(self):
        """
        An array of `asdf.ExternalArrayReference` objects.
        """
        return np.array(self._reference_array[self.parent_slice])

    @property
    def loader_array(self):
        """
        An array of `.BaseParent` objects.

        These loader objects implement the minimal array-like interface for
        conversion to a dask array.
        """
        return np.array(self._loader_array[self.parent_slice])

    @property
    def output_shape(self):
        """
        The final shape of the reconstructed data array.
        """
        return self._output_shape_from_ref_array(self.shape, self.reference_array)

    @property
    def _fileuris(self):
        """
        Numpy array of fileuris
        """
        return np.vectorize(lambda x: x.fileuri)(self.reference_array)

    def _generate_array(self):
        """
        Construct a `dask.array.Array` object from this set of references.

        Each call to this method generates a new array, but all the loaders
        still have a reference to this `~.FileManager` object, meaning changes
        to this object will be reflected in the data loaded by the array.
        """
        return stack_loader_array(self.loader_array).reshape(self.output_shape)


class BaseFileManager:
    @classmethod
    def from_parts(cls, fileuris, target, dtype, shape, *, loader, basepath=None):
        fits_loader = FITSLoader(fileuris, target, dtype, shape, loader=loader, basepath=basepath)
        return cls(fits_loader)

    def __init__(self, fits_loader):
        self._fits_loader = fits_loader
        # When this object is attached to a Dataset object this attribute will
        # be populated with a reference to that Dataset instance.
        self._ndcube = None

    def __eq__(self, other):
        return self._fits_loader == other._fits_loader

    def __getitem__(self, item):
        item = sanitize_slices(item, self._fits_loader.reference_array.ndim)
        return type(self)(FITSLoaderView(self._fits_loader, item))

    def _array_slice_to_reference_slice(self, aslice):
        """
        Convert a slice for the reconstructed array to a slice for the reference_array.
        """
        shape = self._fits_loader.shape
        aslice = list(sanitize_slices(aslice, len(self.output_shape)))
        if shape[0] == 1:
            # Insert a blank slice for the removed dimension
            aslice.insert(len(shape) - 1, slice(None))
        aslice = aslice[len(shape):]
        return tuple(aslice)

    def _slice_by_cube(self, item):
        item = self._array_slice_to_reference_slice(item)
        loader_view = FITSLoaderView(self._fits_loader, item)
        return type(self)(loader_view)

    def _generate_array(self):
        return self._fits_loader._generate_array()

    @property
    def external_array_references(self):
        """
        Represent this collection as a list of `asdf.ExternalArrayReference` objects.
        """
        return self._fits_loader.reference_array.tolist()

    @property
    def basepath(self):
        """
        The path all arrays generated from this ``FileManager`` use to read data from.
        """
        return self._fits_loader.basepath

    @basepath.setter
    def basepath(self, value):
        self._fits_loader.basepath = value

    @property
    def filenames(self):
        """
        Return a list of file names referenced by this Array Container.
        """
        return self._fits_loader._fileuris.flatten().tolist()

    @property
    def output_shape(self):
        return self._fits_loader.output_shape


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
