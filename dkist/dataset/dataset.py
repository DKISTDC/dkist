from textwrap import dedent

import numpy as np

import gwcs
from astropy.wcs.wcsapi.wrappers import SlicedLowLevelWCS

from ndcube.ndcube import NDCube, NDCubeLinkedDescriptor

from dkist.io.file_manager import FileManager
from dkist.utils.decorators import deprecated

from .utils import dataset_info_str

__all__ = ["Dataset"]


class FileManagerDescriptor(NDCubeLinkedDescriptor):
    """
    This is a special version of the NDCubeLinked descriptor which gives a
    FileManager object a reference to the cube when it is assigned to the
    attribute.

    Unlike the upstream code this version does not allow the assignment of a
    class, only an already initialised instance.
    """

    def __get__(self, obj, objtype=None):
        # Override the parent get so that we just return None if not set.
        if obj is None:
            return

        return getattr(obj, self._attribute_name, None)

    def __set__(self, obj, value):
        # Do not allow setting by class not instance.
        if not isinstance(value, self._default_type) and issubclass(value, self._default_type):
            raise ValueError("You must set this property with an instance of FileManager.")

        super().__set__(obj, value)


class Dataset(NDCube):
    """
    The base class for DKIST datasets.

    Parameters
    ----------
    data: `dask.array.Array` or `astropy.nddata.NDData`
        The array holding the actual data in this object.

    wcs: `gwcs.wcs.WCS`, optional
        The WCS object containing the axes' information, optional only if
        ``data`` is an `astropy.nddata.NDData` object.

    uncertainty : any type, optional
        Uncertainty in the dataset. Should have an attribute uncertainty_type
        that defines what kind of uncertainty is stored, for example "std"
        for standard deviation or "var" for variance. A metaclass defining such
        an interface is `~astropy.nddata.NDUncertainty` - but isn't mandatory.
        If the uncertainty has no such attribute the uncertainty is stored as
        `~astropy.nddata.UnknownUncertainty`.
        Defaults to None.

    mask : any type, optional
        Mask for the dataset. Masks should follow the numpy convention
        that valid data points are marked by `False` and invalid ones with `True`.
        Defaults to `None`.

    meta : dict-like object, optional
        Additional meta information about the dataset. If no meta is provided
        an empty dictionary is created.

    unit : Unit-like or `str`, optional
        Unit for the dataset. Strings that can be converted to a
        `~astropy.unit.Unit` are allowed.
        Default is `None` which results in dimensionless units.

    copy : bool, optional
        Indicates whether to save the arguments as copy. `True` copies every
        attribute before saving it while `False` tries to save every parameter
        as reference. Note however that it is not always possible to save the
        input as reference.
        Default is `False`.

    headers : `astropy.table.Table`
        A Table of all FITS headers for all files comprising this dataset.

    Notes
    -----
    When slicing a Dataset instance, both the file manager and the header table
    will also be sliced so that these attributes on the new object refer only
    to the relevant files. However, note that they behave slightly differently.
    The file manager will be a reference to the file manager of the original
    Dataset, meaning that any file name changes made to the sliced object will
    propagate to the original. This is not the case for the header table, as
    slicing creates a new object in this case.
    """

    _file_manager = FileManagerDescriptor(default_type=FileManager)

    def __init__(self, data, wcs=None, uncertainty=None, mask=None, meta=None,
                 unit=None, copy=False):

        # Do some validation
        if (not isinstance(wcs, gwcs.WCS) and
            (isinstance(wcs, SlicedLowLevelWCS) and not isinstance(wcs._wcs, gwcs.WCS))):
            raise ValueError("DKIST Dataset objects expect gWCS objects as the wcs argument.")

        if isinstance(wcs, gwcs.WCS):
            # Set the array shape to be that of the data.
            if wcs.array_shape is None:
                wcs.array_shape = data.shape
            if wcs.pixel_shape is None:
                wcs.pixel_shape = data.shape[::-1]

            if (wcs.pixel_shape != data.shape[::-1] or wcs.array_shape != data.shape):
                raise ValueError("The pixel and array shape on the WCS object "
                                 "do not match the given array.")

        if "headers" not in meta:
            raise ValueError("The meta dict must contain the headers table.")
        if "inventory" not in meta:
            raise ValueError("The meta dict must contain the inventory record.")

        super().__init__(data, wcs, uncertainty=uncertainty, mask=mask, meta=meta,
                         unit=unit, copy=copy)

    def __getitem__(self, item):
        sliced_dataset = super().__getitem__(item)
        if self._file_manager is not None:
            sliced_dataset._file_manager = self._file_manager._slice_by_cube(item)
            sliced_dataset.meta = sliced_dataset.meta.copy()
            sliced_dataset.meta["headers"] = self._slice_headers(item)
        return sliced_dataset

    def _slice_headers(self, slice_):
        idx = self.files._array_slice_to_loader_slice(slice_)
        if idx == (np.s_[:],):
            return self.headers.copy()

        files_shape = [i for i in self.files.fileuri_array.shape if i != 1]
        file_idx = []
        for ax, slc in enumerate(idx):
            if not isinstance(slc, slice):
                slc = slice(slc, slc+1, 1)
            else:
                # mgrid has to have a stop, so if it's missing from the slice we
                # add it.
                stop = slc.stop or files_shape[ax]
                slc = slice(slc.start, stop, slc.step)
            file_idx.append(slc)
        grid = np.mgrid[tuple(file_idx)]
        file_idx = tuple(grid[i].ravel() for i in range(grid.shape[0]))
        flat_idx = np.ravel_multi_index(file_idx[::-1], files_shape[::-1], order="F")

        # Explicitly create new header table to ensure consistency
        # Otherwise would return a reference sometimes and a new table others
        return self.meta["headers"].copy()[flat_idx]

    """
    Properties.
    """

    @property
    def headers(self):
        """
        An `~astropy.table.Table` of all the FITS headers for all files in this dataset.

        .. note::
            This table is read from the asdf file and not from the FITS files,
            so any modifications to the FITS files will not be reflected here.

        """
        return self.meta["headers"]

    @property
    def quality_report(self):
        """
        Information regarding the quality of the observations.
        """
        return self.meta.get("quality", None)

    @property
    def files(self):
        """
        A `~.FileManager` helper for interacting with the files backing the data in this ``Dataset``.
        """
        return self._file_manager

    @property
    def inventory(self):
        """
        Convenience attribute to access the inventory metadata.
        """
        return self.meta["inventory"]

    """
    Dataset loading and saving routines.
    """

    @classmethod
    @deprecated(since="1.0.0", alternative="load_dataset")
    def from_directory(cls, directory):
        """
        Construct a `~dkist.dataset.Dataset` from a directory containing one
        asdf file and a collection of FITS files.
        """
        from .loader import load_dataset
        return load_dataset(directory)

    @classmethod
    @deprecated(since="1.0.0", alternative="load_dataset")
    def from_asdf(cls, filepath):
        """
        Construct a dataset object from a filepath of a suitable asdf file.
        """
        from .loader import load_dataset
        return load_dataset(filepath)

    """
    Private methods.
    """

    def __repr__(self):
        """
        Overload the NDData repr because it does not play nice with the dask delayed io.
        """
        prefix = object.__repr__(self)
        return dedent(f"{prefix}\n{self.__str__()}")

    def __str__(self):
        return dataset_info_str(self)
