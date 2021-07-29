from pathlib import Path
from textwrap import dedent
from importlib import resources

from jsonschema.exceptions import ValidationError
import numpy as np
import asdf
import astropy.table
import gwcs
from astropy.wcs.wcsapi.wrappers import SlicedLowLevelWCS
from ndcube.ndcube import NDCube

from dkist.io import BaseFITSArrayCollection

from .filemanager import FileManager
from .utils import dataset_info_str

__all__ = ['Dataset']


class Dataset(NDCube):
    """
    The base class for DKIST datasets.

    This class is backed by `dask.array.Array` and `gwcs.wcs.WCS` objects.

    Parameters
    ----------
    data: `numpy.ndarray`
        The array holding the actual data in this object.

    wcs: `ndcube.wcs.wcs.WCS`
        The WCS object containing the axes' information

    uncertainty : any type, optional
        Uncertainty in the dataset. Should have an attribute uncertainty_type
        that defines what kind of uncertainty is stored, for example "std"
        for standard deviation or "var" for variance. A metaclass defining
        such an interface is NDUncertainty - but isn’t mandatory. If the uncertainty
        has no such attribute the uncertainty is stored as UnknownUncertainty.
        Defaults to None.

    mask : any type, optional
        Mask for the dataset. Masks should follow the numpy convention
        that valid data points are marked by False and invalid ones with True.
        Defaults to None.

    meta : dict-like object, optional
        Additional meta information about the dataset. If no meta is provided
        an empty collections.OrderedDict is created. Default is None.

    unit : Unit-like or str, optional
        Unit for the dataset. Strings that can be converted to a Unit are allowed.
        Default is None.

    extra_coords : iterable of `tuple`, each with three entries
        (`str`, `int`, `astropy.units.quantity` or array-like)
        Gives the name, axis of data, and values of coordinates of a data axis not
        included in the WCS object.

    headers : `astropy.table.Table`
        A Table of all FITS headers for all files comprising this dataset.
    """

    def __init__(self, data, wcs=None, uncertainty=None, mask=None, meta=None,
                 unit=None, copy=False, headers=None):

        if isinstance(data, FileManager):
            self._files = data
        elif isinstance(data, BaseFITSArrayCollection):
            self._files = FileManager(data)
        else:
            raise TypeError("The Dataset object must be instantiated with an "
                            "ArrayCollection or FileManager object as the data.")

        # We need to trick the NDData constructor
        data = np.empty((0,))

        # Do some validation
        if (not isinstance(wcs, gwcs.WCS) and
            (isinstance(wcs, SlicedLowLevelWCS) and not isinstance(wcs._wcs, gwcs.WCS))):
            raise ValueError("DKIST Dataset objects expect gWCS objects as the wcs argument.")

        if isinstance(wcs, gwcs.WCS):
            # Set the array shape to be that of the data.
            if wcs.array_shape is None:
                wcs.array_shape = self.data.shape

            if wcs.pixel_shape is None:
                wcs.pixel_shape = self.data.shape[::-1]

            if (wcs.pixel_shape != self.data.shape[::-1] or wcs.array_shape != self.data.shape):
                raise ValueError("The pixel and array shape on the WCS object "
                                 "do not match the given array.")

        if headers is not None and not isinstance(headers, astropy.table.Table):
            raise ValueError("The headers keyword argument must be an Astropy Table instance.")

        super().__init__(data, wcs, uncertainty=uncertainty, mask=mask, meta=meta,
                         unit=unit, copy=copy)

        # The upstream constructor set's the fake array we gave it to the
        # hidden _data property.
        self._data = None
        self._header_table = headers

    def _slice(self, item):
        """
        Customise the slicing of the "data" argument.
        """
        kwargs = super()._slice(item)
        kwargs['data'] = self.files._get_array_item(item)
        return kwargs

    """
    Properties.
    """

    @property
    def files(self):
        return self._files

    @property
    def data(self):
        return self._files.data

    @property
    def headers(self):
        return self._header_table

    """
    Dataset loading and saving routines.
    """

    @classmethod
    def from_directory(cls, directory):
        """
        Construct a `~dkist.dataset.Dataset` from a directory containing one
        asdf file and a collection of FITS files.
        """
        base_path = Path(directory)
        if not base_path.is_dir():
            raise ValueError("directory argument must be a directory")
        asdf_files = tuple(base_path.glob("*.asdf"))

        if not asdf_files:
            raise ValueError("No asdf file found in directory.")
        elif len(asdf_files) > 1:
            raise NotImplementedError("Multiple asdf files found in this "
                                      "directory. Use from_asdf to specify which "
                                      "one to use.") # pragma: no cover

        asdf_file = asdf_files[0]

        return cls.from_asdf(asdf_file)

    @classmethod
    def from_asdf(cls, filepath):
        """
        Construct a dataset object from a filepath of a suitable asdf file.
        """
        filepath = Path(filepath)
        base_path = filepath.parent
        try:
            with resources.path("dkist.io", "level_1_dataset_schema.yaml") as schema_path:
                with asdf.open(filepath, custom_schema=schema_path.as_posix(),
                               lazy_load=False, copy_arrays=True) as ff:
                    return ff.tree['dataset']

        except ValidationError as e:
            err = f"This file is not a valid DKIST Level 1 asdf file, it fails validation with: {e.message}."
            raise TypeError(err) from e

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
