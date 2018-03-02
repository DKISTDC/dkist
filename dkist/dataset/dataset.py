import copy
import glob
import os.path
from pathlib import Path

import asdf
import numpy as np

import astropy.units as u

from ndcube.ndcube import NDCubeBase


from dkist.dataset.mixins import DatasetPlotMixin
from dkist.io import DaskFITSArrayContainer, AstropyFITSLoader

__all__ = ['Dataset']


class Dataset(DatasetPlotMixin, NDCubeBase):
    """
    The base class for DKIST datasets.

    This class is backed by `dask.array.Array` and `gwcs.wcs.WCS` objects.
    """

    @classmethod
    def from_directory(cls, directory):
        """
        Construct a `~dkist.dataset.Dataset` from a directory containing one
        asdf file and a collection of FITS files.
        """
        if not os.path.isdir(directory):
            raise ValueError("directory argument must be a directory")
        base_path = Path(directory)
        asdf_files = glob.glob(str(base_path / "*.asdf"))

        if not asdf_files:
            raise ValueError("No asdf file found in directory.")
        elif len(asdf_files) > 1:
            raise NotImplementedError("Multiple asdf files found in this"
                                      " directory. Can't handle this yet.")

        asdf_file = asdf_files[0]

        with asdf.AsdfFile.open(asdf_file) as ff:
            # TODO: without this it segfaults on access
            asdf_tree = copy.deepcopy(ff.tree)
            pointer_array = np.array(ff.tree['dataset'])

        array_container = DaskFITSArrayContainer(pointer_array, loader=AstropyFITSLoader,
                                                 basepath=str(base_path))

        data = array_container.array

        wcs = asdf_tree['gwcs']

        return cls(data, wcs=wcs)

    def __repr__(self):
        """
        Overload the NDData repr because it does not play nice with the dask delayed io.
        """
        prefix = self.__class__.__name__ + '('
        body = str(self.data)
        return ''.join([prefix, body, ')'])

    def pixel_to_world(self, *quantity_axis_list):
        """
        Convert a pixel coordinate to a data (world) coordinate by using
        `~gwcs.wcs.WCS`.

        Parameters
        ----------
        quantity_axis_list : iterable
            An iterable of `~astropy.units.Quantity` with unit as pixel `pix`.
            Note that these quantities must be entered as separate arguments, not as one list.

        Returns
        -------
        coord : `list`
            A list of arrays containing the output coordinates.
        """
        return tuple(self.wcs(*quantity_axis_list, output='numericals_plus'))

    def world_to_pixel(self, *quantity_axis_list):
        """
        Convert a world coordinate to a data (pixel) coordinate by using
        `~gwcs.wcs.WCS.invert`.

        Parameters
        ----------
        quantity_axis_list : iterable
            A iterable of `~astropy.units.Quantity`.
            Note that these quantities must be entered as separate arguments, not as one list.

        Returns
        -------
        coord : `list`
            A list of arrays containing the output coordinates.
        """
        return tuple(self.wcs.invert(*quantity_axis_list, output="numericals_plus"))

    def world_axis_physical_types(self):
        raise NotImplementedError()

    @property
    def dimensions(self):
        """
        The dimensions of the data as a `~astropy.units.Quantity`.
        """
        return u.Quantity(self.data.shape, unit=u.pix)

    def crop_by_coords(self, min_coord_values, interval_widths):
        # The docstring is defined in NDDataBase

        n_dim = len(self.dimensions)
        if len(min_coord_values) != len(interval_widths) != n_dim:
            raise ValueError("min_coord_values and interval_widths must have "
                             "same number of elements as number of data dimensions.")
        # Convert coords of lower left corner to pixel units.
        lower_pixels = self.world_to_pixel(*min_coord_values)
        upper_pixels = self.world_to_pixel(*[min_coord_values[i] + interval_widths[i]
                                             for i in range(len(min_coord_values))])
        # Round pixel values to nearest integer.
        lower_pixels = [int(np.rint(l.value)) for l in lower_pixels]
        upper_pixels = [int(np.rint(u.value)) for u in upper_pixels]
        item = tuple([slice(lower_pixels[i], upper_pixels[i]) for i in range(n_dim)])
        return self.data[item]
