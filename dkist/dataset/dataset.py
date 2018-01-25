import glob
import os.path
from pathlib import Path

import asdf
import numpy as np

from ndcube.ndcube import NDCubeBase

from asdf.tags.core.external_reference import ExternalArrayReference

from ..io import DaskFITSArrayContainer, AstropyFITSLoader

__all__ = ['Dataset']


class Dataset(NDCubeBase):
    """
    Load a DKIST dataset.

    Parameters
    ----------

    directory : `str`
        The directory holding the dataset.
    """

    @classmethod
    def from_directory(cls, directory):
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

    """
    Methods to be implemented.
    """
    def pixel_to_world(self, quantity_axis_list, origin=0):
        raise NotImplementedError()

    def world_to_pixel(self, quantity_axis_list, origin=0):
        raise NotImplementedError()

    def dimensions(self):
        raise NotImplementedError()

    def crop_by_coords(self, lower_left_corner, dimension_widths):
        raise NotImplementedError()
