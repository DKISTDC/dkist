"""
Tiled datasets are one dataset which is made up of multiple smaller datasets tiled in space.

A tiled dataset is a "dataset" in terms of how it's provided by the DKIST DC,
but not representable in a single NDCube derived object as the array data are
not contiguous in the spatial dimensions (due to overlaps and offsets).
"""

__all__ = ['TiledDataset']


class TiledDataset:
    """
    A class for holding a dataset where the spatial axes are tiled.
    """

    def __init__(self, dataset_array, meta=None):
        self._data = np.array(dataset_array, dtype=object)
        if not self._validate_component_datasets(self._data):
            raise ValueError("All component datasets must have the same physical types")
        self._meta = meta

    @staticmethod
    def _validate_component_datasets(datasets):
        datasets = datasets.flat
        pt_1 = datasets[0].world_axis_physical_types
        for ds in datasets[1:]:
            if ds.world_axis_physical_types != pt_1:
                return False
        return True

    @property
    def meta(self):
        return self._meta

    def __getitem__(self, aslice):
        new_data = self._data[aslice]
        if len(new_data) == 1:
            return new_data

        return type(self)(new_data, meta=self.meta)
