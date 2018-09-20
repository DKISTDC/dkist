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

    def crop_by_coords(self, lower_corner, upper_corner, units=None):
        """
        Crops an NDCube given the lower and upper corners of a box in world coordinates.

        Parameters
        ----------
        lower_corner: iterable of `astropy.units.Quantity` or `float`
            The minimum desired values along each relevant axis after cropping
            described in physical units consistent with the NDCube's wcs object.
            The length of the iterable must equal the number of data dimensions
            and must have the same order as the data.
        upper_corner: iterable of `astropy.units.Quantity` or `float`
            The maximum desired values along each relevant axis after cropping
            described in physical units consistent with the NDCube's wcs object.
            The length of the iterable must equal the number of data dimensions
            and must have the same order as the data.
        units: iterable of `astropy.units.quantity.Quantity`, optional
            If the inputs are set without units, the user must set the units
            inside this argument as `str`.
            The length of the iterable must equal the number of data dimensions
            and must have the same order as the data.

        Returns
        -------
        result: NDCube
        """
        n_dim = self.data.ndim
        if units:
            # Raising a value error if units have not the data dimensions.
            if len(units) != n_dim:
                raise ValueError('units must have same number of elements as '
                                 'number of data dimensions.')
            # If inputs are not Quantity objects, they are modified into specified units
            lower_corner = [u.Quantity(lower_corner[i], unit=units[i])
                            for i in range(self.data.ndim)]
            upper_corner = [u.Quantity(upper_corner[i], unit=units[i])
                            for i in range(self.data.ndim)]
        else:
            if any([not isinstance(x, u.Quantity) for x in lower_corner] +
                   [not isinstance(x, u.Quantity) for x in upper_corner]):
                raise TypeError("lower_corner and interval_widths/upper_corner must be "
                                "of type astropy.units.Quantity or the units kwarg "
                                "must be set.")
        # Get all corners of region of interest.
        all_world_corners_grid = np.meshgrid(
            *[u.Quantity([lower_corner[i], upper_corner[i]], unit=lower_corner[i].unit).value
              for i in range(self.data.ndim)])
        all_world_corners = [all_world_corners_grid[i].flatten()*lower_corner[i].unit
                             for i in range(n_dim)]
        # Convert to pixel coordinates
        all_pix_corners = self.wcs(*all_world_corners, with_units=False)
        # Derive slicing item with which to slice NDCube.
        # Be sure to round down min pixel and round up + 1 the max pixel.
        item = tuple([slice(int(np.clip(axis_pixels.value.min(), 0, None)),
                            int(np.ceil(axis_pixels.value.max()))+1)
                      for axis_pixels in all_pix_corners])
        return self[item]
