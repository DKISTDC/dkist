import copy
import glob
import os.path
from pathlib import Path
from textwrap import dedent

import numpy as np

import asdf
import astropy.units as u
from astropy.utils import isiterable
from ndcube.ndcube import NDCubeABC

from dkist.io import AstropyFITSLoader, DaskFITSArrayContainer
from dkist.dataset.mixins import DatasetPlotMixin, DatasetSlicingMixin

__all__ = ['Dataset']


class Dataset(DatasetSlicingMixin, DatasetPlotMixin, NDCubeABC):
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
                                      " directory. Can't handle this yet.")  # pragma: no cover

        asdf_file = asdf_files[0]

        return cls.from_asdf(asdf_file)

    @classmethod
    def from_asdf(cls, filepath):
        """
        Construct a dataset object from a filepath of a suitable asdf file.
        """
        filepath = Path(filepath)
        base_path = filepath.parent
        with asdf.AsdfFile.open(str(filepath)) as ff:
            # TODO: without this it segfaults on access
            asdf_tree = copy.deepcopy(ff.tree)
            pointer_array = np.array(ff.tree['dataset'])

        array_container = DaskFITSArrayContainer(pointer_array, loader=AstropyFITSLoader,
                                                 basepath=str(base_path))

        data = array_container.array

        wcs = asdf_tree['gwcs']

        return cls(data, wcs=wcs)

    @property
    def pixel_axes_names(self):
        if self.wcs.input_frame:
            return self.wcs.input_frame.axes_names[::-1]
        else:
            return ('',) * self.data.ndim

    @property
    def world_axes_names(self):
        if self.wcs.output_frame:
            return self.wcs.output_frame.axes_names[::-1]
        else:
            return ('',)*self.data.ndim  # pragma: no cover  # We should never hit this

    def __repr__(self):
        """
        Overload the NDData repr because it does not play nice with the dask delayed io.
        """
        prefix = object.__repr__(self)

        pnames = ', '.join(self.pixel_axes_names)
        wnames = ', '.join(self.world_axes_names)
        output = dedent(f"""\
        {prefix}
        {self.data!r}
        WCS<pixel_axes_names=({pnames}),
            world_axes_names=({wnames})>""")
        return output

    def pixel_to_world(self, *quantity_axis_list):
        """
        Convert a pixel coordinate to a data (world) coordinate by using
        `~gwcs.wcs.WCS`.

        This method expects input and returns output in the same order as the
        array dimensions. (Which is the reverse of the underlying WCS object.)

        Parameters
        ----------
        quantity_axis_list : iterable
            An iterable of `~astropy.units.Quantity` with unit as pixel `pix`.

        Returns
        -------
        coord : `list`
            A list of arrays containing the output coordinates.
        """
        world = self.wcs(*quantity_axis_list[::-1], with_units=True)

        # Convert list to tuple as a more standard return type
        if isinstance(world, list):
            world = tuple(world)

        # If our return is an iterable then reverse it to match pixel dims.
        if isiterable(world):
            return world[::-1]

        return world

    def world_to_pixel(self, *quantity_axis_list):
        """
        Convert a world coordinate to a data (pixel) coordinate by using
        `~gwcs.wcs.WCS.invert`.

        This method expects input and returns output in the same order as the
        array dimensions. (Which is the reverse of the underlying WCS object.)

        Parameters
        ----------
        quantity_axis_list : iterable
            A iterable of `~astropy.units.Quantity`.

        Returns
        -------
        coord : `list`
            A list of arrays containing the output coordinates.
        """
        return tuple(self.wcs.invert(*quantity_axis_list[::-1], with_units=True))[::-1]

    def world_axis_physical_types(self):
        raise NotImplementedError()  # pragma: no cover

    @property
    def dimensions(self):
        """
        The dimensions of the data as a `~astropy.units.Quantity`.
        """
        return u.Quantity(self.data.shape, unit=u.pix)

    def crop_by_coords(self, min_coord_values, interval_widths):
        # The docstring is defined in NDDataBase

        n_dim = len(self.dimensions)
        if (len(min_coord_values) != len(interval_widths)) or len(min_coord_values) != n_dim:
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
        return self[item]
