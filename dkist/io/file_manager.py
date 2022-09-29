"""
Utilities for backing an ``NDCube`` with an array striped across many FITS files.

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
from typing import Any, List, Tuple, Union, Iterable, Optional
from pathlib import Path

import dask.array
import numpy as np

try:
    from numpy.typing import DTypeLike, NDArray  # NOQA
except ImportError:
    NDArray = DTypeLike = Iterable

from asdf.tags.core.external_reference import ExternalArrayReference
from astropy.wcs.wcsapi.wrappers.sliced_wcs import sanitize_slices

from dkist.io.dask_utils import stack_loader_array
from dkist.io.loaders import BaseFITSLoader
from dkist.net import conf as net_conf
from dkist.net.helpers import _orchestrate_transfer_task
from dkist.utils.inventory import humanize_inventory, path_format_inventory


class BaseStripedExternalArray:
    """
    Implements shared functionality between FITSLoader and FITSLoaderView.
    """

    def __len__(self) -> int:
        return self.reference_array.size

    def __eq__(self, other) -> bool:
        uri = (self.reference_array == other.reference_array).all()
        target = self.target == other.target
        dtype = self.dtype == other.dtype
        shape = self.shape == other.shape

        return all((uri, target, dtype, shape))

    @staticmethod
    def _output_shape_from_ref_array(shape, reference_array) -> Tuple[int]:
        # If the first dimension is one we are going to squash it.
        if shape[0] == 1:
            shape = shape[1:]

        if len(reference_array) == 1:
            return shape
        else:
            return tuple(list(reference_array.shape) + list(shape))

    @property
    def output_shape(self) -> Tuple[int, ...]:
        """
        The final shape of the reconstructed data array.
        """
        return self._output_shape_from_ref_array(self.shape, self.reference_array)

    @property
    def _fileuris(self) -> NDArray[str]:
        """
        Numpy array of fileuris
        """
        return np.vectorize(lambda x: x.fileuri)(self.reference_array)

    def _generate_array(self) -> dask.array.Array:
        """
        Construct a `dask.array.Array` object from this set of references.

        Each call to this method generates a new array, but all the loaders
        still have a reference to this `~.FileManager` object, meaning changes
        to this object will be reflected in the data loaded by the array.
        """
        return stack_loader_array(self.loader_array).reshape(self.output_shape)


class StripedExternalArray(BaseStripedExternalArray):
    def __init__(
        self,
        fileuris: Iterable[str],
        target: Any,
        dtype: DTypeLike,
        shape: Iterable[int],
        *,
        loader: BaseFITSLoader,
        basepath: os.PathLike = None,
    ):
        shape = tuple(shape)
        self.shape = shape
        self.dtype = dtype
        self.target = target
        self._loader = loader
        self._basepath = None
        self.basepath = basepath  # Use the setter to convert to a Path

        self._reference_array = np.vectorize(
            lambda uri: ExternalArrayReference(uri, self.target, self.dtype, self.shape)
        )(fileuris)

        loader_array = np.empty_like(self.reference_array, dtype=object)
        for i, ele in enumerate(self.reference_array.flat):
            loader_array.flat[i] = loader(ele, self)

        self._loader_array = loader_array

    def __str__(self) -> str:
        return f"FITSLoader {len(self)} files with shape {self.shape}"

    def __repr__(self) -> str:
        return f"{object.__repr__(self)}\n{self}"

    @property
    def basepath(self) -> os.PathLike:
        """
        The path all arrays generated from this ``FileManager`` use to read data from.
        """
        return self._basepath

    @basepath.setter
    def basepath(self, value: Optional[Union[os.PathLike, str]]):
        self._basepath = Path(value).expanduser() if value is not None else None

    @property
    def reference_array(self) -> NDArray[ExternalArrayReference]:
        """
        An array of `asdf.ExternalArrayReference` objects.
        """
        return self._reference_array

    @property
    def loader_array(self) -> NDArray[BaseFITSLoader]:
        """
        An array of `.BaseFITSLoader` objects.

        These loader objects implement the minimal array-like interface for
        conversion to a dask array.
        """
        return self._loader_array

    def _to_ears(self, urilist) -> List[ExternalArrayReference]:
        # This is separate to the property because it's recursive
        if isinstance(urilist, (list, tuple)):
            return list(map(self._to_ears, urilist))
        return ExternalArrayReference(urilist, self.target, self.dtype, self.shape)


class StripedExternalArrayView(BaseStripedExternalArray):
    # This class presents a view int a FITSLoader object It applies a slice to
    # the reference_array and loader_array properties Any property which
    # references the sliced objects should be defined in Base or this view
    # class.
    __slots__ = ["parent", "parent_slice"]

    def __init__(self, parent: StripedExternalArray, aslice: Union[tuple, slice, int]):
        self.parent = parent
        self.parent_slice = tuple(aslice)

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
    def reference_array(self) -> NDArray[ExternalArrayReference]:
        """
        An array of `asdf.ExternalArrayReference` objects.
        """
        return np.array(self._reference_array[self.parent_slice])

    @property
    def loader_array(self) -> NDArray[BaseFITSLoader]:
        """
        An array of `.BaseParent` objects.

        These loader objects implement the minimal array-like interface for
        conversion to a dask array.
        """
        return np.array(self._loader_array[self.parent_slice])


class BaseFileManager:
    @classmethod
    def from_parts(cls, fileuris, target, dtype, shape, *, loader, basepath=None):
        fits_loader = StripedExternalArray(
            fileuris, target, dtype, shape, loader=loader, basepath=basepath
        )
        return cls(fits_loader)

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
        item = sanitize_slices(item, self._striped_external_array.reference_array.ndim)
        return type(self)(StripedExternalArrayView(self._striped_external_array, item))

    def _array_slice_to_reference_slice(self, aslice):
        """
        Convert a slice for the reconstructed array to a slice for the reference_array.
        """
        fits_array_shape = self._striped_external_array.shape
        aslice = list(sanitize_slices(aslice, len(self.output_shape)))
        if fits_array_shape[0] == 1:
            # Insert a blank slice for the dummy dimension
            aslice.insert(len(fits_array_shape) - 1, slice(None))
        # Now only use the dimensions of the slice not covered by the array axes
        aslice = aslice[:-1*len(fits_array_shape)]
        return tuple(aslice)

    def _slice_by_cube(self, item):
        item = self._array_slice_to_reference_slice(item)
        loader_view = StripedExternalArrayView(self._striped_external_array, item)
        return type(self)(loader_view)

    def _generate_array(self):
        return self._striped_external_array._generate_array()

    @property
    def external_array_references(self):
        """
        Represent this collection as a list of `asdf.ExternalArrayReference` objects.
        """
        return self._striped_external_array.reference_array.tolist()

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
        return self._striped_external_array._fileuris.flatten().tolist()

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


class FileManager(BaseFileManager):
    """
    Manage the collection of FITS files backing a `~dkist.Dataset`.

    Each `~dkist.Dataset` object is backed by a number of FITS files, each holding a
    slice of the total array. This class provides tools for inspecting and
    retrieving these FITS files, as well as specifying where to load these
    files from.
    """

    def __init__(self, fits_loader: StripedExternalArray):
        super().__init__(fits_loader)
        # When this object is attached to a Dataset object this attribute will
        # be populated with a reference to that Dataset instance.
        self._ndcube = None

    def download(self, path=None, destination_endpoint=None, progress=True, wait=True, label=None):
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
            If ``path`` is specified, and ``destination_endpoint`` is `None`
            (i.e. you are downloading to a local Globus personal endpoint) this
            method will set ``.basepath`` to the value of the ``path=``
            argument, so that the array can be read from your transferred
            files.

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

        label : `str`
            Label for the Globus transfer. If `None` then a default will be used.
        """
        if self._ndcube is None:
            raise ValueError(
                "This file manager has no associated Dataset object, so the data can not be downloaded."
            )

        inv = self._ndcube.meta["inventory"]
        path_inv = path_format_inventory(humanize_inventory(inv))

        base_path = Path(net_conf.dataset_path.format(**inv))
        destination_path = path or self.basepath or "/~/"
        destination_path = Path(destination_path).as_posix()
        destination_path = Path(destination_path.format(**path_inv))

        # TODO: If we are transferring the whole dataset then we should use the
        # directory not the list of all the files in it.
        file_list = [base_path / fn for fn in self.filenames]
        file_list.append(Path("/") / inv["bucket"] / inv["asdfObjectKey"])
        if inv["browseMovieObjectKey"]:
            file_list.append(Path("/") / inv["bucket"] / inv["browseMovieObjectKey"])
        if inv["qualityReportObjectKey"]:
            file_list.append(Path("/") / inv["bucket"] / inv["qualityReportObjectKey"])

        # TODO: Ascertain if the destination path is local better than this
        is_local = not destination_endpoint

        _orchestrate_transfer_task(
            file_list,
            recursive=False,
            destination_path=destination_path,
            destination_endpoint=destination_endpoint,
            progress=progress,
            wait=wait,
            label=label
        )

        if is_local:
            if str(destination_path).startswith("/~/"):
                local_destination = Path(str(destination_path)[1:])
            local_destination = destination_path.expanduser()
            self.basepath = local_destination
