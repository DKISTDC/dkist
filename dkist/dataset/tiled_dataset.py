"""
Tiled datasets are one dataset which is made up of multiple smaller datasets tiled in space.

A tiled dataset is a "dataset" in terms of how it's provided by the DKIST DC,
but not representable in a single NDCube derived object as the array data are
not contiguous in the spatial dimensions (due to overlaps and offsets).
"""
from collections.abc import Collection

import numpy as np

from astropy.table import vstack

from .dataset import Dataset

__all__ = ['TiledDataset']


class TiledDataset(Collection):
    """
    A class for holding a dataset where the spatial axes are tiled.
    """

    @classmethod
    def _from_components(cls, shape, file_managers, wcses, header_tables, inventory):
        """
        Construct a TiledDataset from the component parts of all the sub-datasets.

        This is intended to be used in the dkist-inventory package for creating
        these objects to be saved to asdf.

        The inputs need to be in numpy order, as the flat list of datasets will
        be reshaped into the given shape.
        """
        assert len(file_managers) == len(wcses) == len(header_tables)

        datasets = np.empty(len(file_managers), dtype=object)
        for i, (fm, wcs, headers) in enumerate(zip(file_managers, wcses, header_tables)):
            meta = {"inventory": inventory, "headers": headers}
            datasets[i] = Dataset(fm._generate_array(), wcs=wcs, meta=meta)
            datasets[i]._file_manager = fm
        datasets = datasets.reshape(shape)

        return cls(datasets, inventory)

    def __init__(self, dataset_array, inventory={}):
        self._data = np.array(dataset_array, dtype=object)
        self._inventory = inventory
        if not self._validate_component_datasets(self._data, inventory):
            raise ValueError("All component datasets must have the same physical types and inventory dict")

    def __contains__(self, x):
        return self._data.__contains__(x)

    def __len__(self):
        return self._data.__len__()

    def __iter__(self):
        self._data.__iter__()

    @staticmethod
    def _validate_component_datasets(datasets, inventory):
        datasets = datasets.flat
        inv_1 = datasets[0].meta["inventory"]
        if inv_1 and inv_1 is not inventory:
            return False
        pt_1 = datasets[0].wcs.world_axis_physical_types
        for ds in datasets[1:]:
            if ds.wcs.world_axis_physical_types != pt_1:
                return False
            if ds.meta["inventory"] and ds.meta["inventory"] is not inventory:
                return False
        return True

    @property
    def meta(self):
        return self._meta

    @property
    def combined_headers(self):
        return vstack([ds.meta["headers"] for ds in self._data.flat])

    @property
    def shape(self):
        return self._data.shape

    def __getitem__(self, aslice):
        new_data = self._data[aslice]
        if isinstance(new_data, Dataset):
            return new_data

        return type(self)(new_data, meta=self.meta)
