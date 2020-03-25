from pathlib import Path
from textwrap import dedent

from jsonschema.exceptions import ValidationError

import asdf
import astropy.table
import gwcs
from astropy.visualization.wcsaxes import WCSAxes
from astropy.wcs.wcsapi import SlicedLowLevelWCS
from ndcube.ndcube import NDCube

from dkist.io import DaskFITSArrayContainer
from dkist.utils.globus import (DKIST_DATA_CENTRE_DATASET_PATH, DKIST_DATA_CENTRE_ENDPOINT_ID,
                                start_transfer_from_file_list, watch_transfer_progress)
from dkist.utils.globus.endpoints import get_local_endpoint_id, get_transfer_client

from .utils import dataset_info_str

try:
    from importlib import resources  # >= py 3.7
except ImportError:
    import importlib_resources as resources


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

    def __init__(self, data, wcs, uncertainty=None, mask=None, meta=None,
                 unit=None, extra_coords=None, headers=None):

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

        if headers is not None and not isinstance(headers, astropy.table.Table):
            raise ValueError("The headers keyword argument must be an Astropy Table instance.")

        super().__init__(data, wcs, uncertainty=uncertainty, mask=mask, meta=meta,
                         unit=unit, extra_coords=extra_coords, copy=False)

        self._header_table = headers
        self._array_container = None

    """
    Changes to the NDCube APIs.
    """

    # Overload this to only expose the new API in this package, this can be
    # removed once NDCube 2 is finalised.
    def crop_by_coords(self, lower_corner, upper_corner, units=None):
        return super().crop_by_coords(lower_corner, upper_corner=upper_corner, units=units)

    @property
    def world_axis_physical_types(self):
        """
        Returns an iterable of strings describing the physical type for each world axis.

        The strings conform to the International Virtual Observatory Alliance
        standard, UCD1+ controlled Vocabulary.  For a description of the standard and
        definitions of the different strings and string components,
        see http://www.ivoa.net/documents/latest/UCDlist.html.

        """
        return self.wcs.world_axis_physical_types[::-1]

    """
    Properties.
    """

    @property
    def headers(self):
        return self._header_table

    @property
    def array_container(self):
        """
        A reference to the files containing the data.
        """
        return self._array_container

    @property
    def filenames(self):
        """
        The filenames referenced by this dataset.

        .. note::
            This is not their full file paths.
        """
        if self._array_container is None:
            return []
        else:
            return self._array_container.filenames

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

    def _as_mpl_axes(self):
        """
        Allow this object to be passed to matplotlib as a projection.
        """
        return WCSAxes, {'transform': self.wcs}

    """
    DKIST specific methods.
    """

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

        base_path = DKIST_DATA_CENTRE_DATASET_PATH.format(**self.meta)
        # TODO: Default path to the config file
        destination_path = Path(path) / self.meta['dataset_id']

        file_list = [Path(base_path) / fn for fn in self.filenames]
        file_list.append(Path(base_path) / self.meta['asdf_object_key'])

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
        old_ac = self._array_container
        self._array_container = DaskFITSArrayContainer.from_external_array_references(
            old_ac.external_array_references,
            loader=old_ac._loader,
            basepath=destination_path)
        self._data = self._array_container.array
