import glob
import os.path
from pathlib import Path

from ndcube.ndcube import NDCubeBase


class Dataset(NDCubeBase):
    """
    Load a DKIST dataset.

    Parameters
    ----------

    directory : `str`
        The directory holding the dataset.
    """

    def __init__(self, directory):
        if not os.path.isdir(directory):
            raise ValueError("directory argument must be a directory")
        self.base_path = Path(directory)
        asdf_files = glob.glob(self.base_path / "*.asdf")

        if not asdf_files:
            raise ValueError("No asdf file found in directory.")
        elif len(asdf_files) > 1:
            raise NotImplementedError("Multiple asdf files found in this"
                                      " directory. Can't handle this yet.")

        self.asdf_file = asdf_files[0]

        # super().__init__(self, data, wcs)

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
