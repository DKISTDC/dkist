from textwrap import dedent

import gwcs
from astropy.wcs.wcsapi.wrappers import SlicedLowLevelWCS
from ndcube.ndcube import NDCube, NDCubeLinkedDescriptor

from dkist.io.file_manager import FileManager

from .utils import dataset_info_str

__all__ = ['Dataset']


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
        an interface is `~astropy.nddata.NDUncertainty` - but isn’t mandatory.
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
        return sliced_dataset

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
        Convenience attribute to acces the inventory metadata.
        """
        return self.meta['inventory']

    """
    Private methods.
    """

    def __repr__(self):
        """
        Overload the NDData repr because it does not play nice with the dask delayed io.
        """
        prefix = object.__repr__(self)
        output = dedent(f"{prefix}\n{self.__str__()}")
        return output

    def __str__(self):
        return dataset_info_str(self)
