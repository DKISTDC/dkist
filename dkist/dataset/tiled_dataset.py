"""
Tiled datasets are one dataset which is made up of multiple smaller datasets tiled in space.

A tiled dataset is a "dataset" in terms of how it's provided by the DKIST DC,
but not representable in a single NDCube derived object as the array data are
not contiguous in the spatial dimensions (due to overlaps and offsets).
"""
from textwrap import dedent
from collections.abc import Collection

import matplotlib.pyplot as plt
import numpy as np

from astropy.table import vstack

from .dataset import Dataset
from .utils import dataset_info_str

__all__ = ["TiledDataset"]


class TiledDatasetSlicer:
    """
    Basic class to provide the slicing
    """
    def __init__(self, data, inventory):
        self.data = data
        self.inventory = inventory

    def __getitem__(self, slice_):
        new_data = []
        for tile in self.data.flat:
            new_data.append(tile[slice_])
        return TiledDataset(np.array(new_data).reshape(self.data.shape), self.inventory)


class TiledDataset(Collection):
    """
    Holds a grid of `.Dataset` objects.

    In the case where multiple images are taken in different locations on the
    sky and the images do not share a common pixel grid they can not be
    represented as a single `.Dataset` object.
    This class represented these tiled or "mosaicked" data can be regridded to
    be represented as a single `.Dataset`, but this involves some level of
    interpolation, so it is not always done by default.

    This `.TiledDataset` class can be sliced in an array-like fashion to
    extract one or more `.Dataset` objects given their location in the grid.

    .. note::

        This class does not currently implement helper functions to regrid the
        data. This functionality will be added in the future, see the reproject
        and montage packages for possible ways to achieve this.

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

    def __init__(self, dataset_array, inventory=None):
        self._data = np.array(dataset_array, dtype=object)
        self._inventory = inventory or {}
        self._validate_component_datasets(self._data, inventory)

    def __contains__(self, x):
        return any(ele is x for ele in self._data.flat)

    def __len__(self):
        return self._data.__len__()

    def __iter__(self):
        return self._data.__iter__()

    def __getitem__(self, aslice):
        new_data = self._data[aslice]
        if isinstance(new_data, Dataset):
            return new_data

        return type(self)(new_data, inventory=self.inventory)

    @staticmethod
    def _validate_component_datasets(datasets, inventory):
        datasets = datasets.flat
        inv_1 = datasets[0].meta["inventory"]
        if inv_1 and inv_1 is not inventory:
            raise ValueError("The inventory record of the first dataset does not match the one passed to TiledDataset")
        pt_1 = datasets[0].wcs.world_axis_physical_types
        for ds in datasets[1:]:
            if ds.wcs.world_axis_physical_types != pt_1:
                raise ValueError("The physical types do not match between all datasets")
            if ds.meta["inventory"] and ds.meta["inventory"] is not inventory:
                raise ValueError("The inventory records of all the datasets do not match the one passed to TiledDataset")
        return True

    @property
    def flat(self):
        """
        Represent this `.TiledDataset` as a 1D array.
        """
        return type(self)(self._data.flat, self.inventory)

    @property
    def inventory(self):
        """
        The inventory record as kept by the data center for this dataset.
        """
        return self._inventory

    @property
    def combined_headers(self):
        """
        A single `astropy.table.Table` containing all the FITS headers for all
        files in this dataset.
        """
        return vstack([ds.meta["headers"] for ds in self._data.flat])

    @property
    def shape(self):
        """
        The shape of the tiled grid.
        """
        return self._data.shape

    @property
    def tiles_shape(self):
        """
        The shape of each individual tile in the TiledDataset.
        """
        return [[tile.data.shape for tile in row] for row in self]

    def plot(self, slice_index: int, share_zscale=False, **kwargs):
        vmin, vmax = np.inf, 0
        fig = plt.figure()
        for i, tile in enumerate(self.flat):
            ax = fig.add_subplot(self.shape[0], self.shape[1], i+1, projection=tile[0].wcs)
            tile[slice_index].plot(axes=ax, **kwargs)
            if i == 0:
                xlabel = ax.coords[0].get_axislabel() or ax.coords[0]._get_default_axislabel()
                ylabel = ax.coords[1].get_axislabel() or ax.coords[1]._get_default_axislabel()
                for coord in ax.coords:
                    if "b" in coord.axislabels.get_visible_axes():
                        fig.supxlabel(xlabel, y=0.05)
                    if "l" in coord.axislabels.get_visible_axes():
                        fig.supylabel(ylabel, x=0.05)
            axmin, axmax = ax.get_images()[0].get_clim()
            vmin = axmin if axmin < vmin else vmin
            vmax = axmax if axmax > vmax else vmax
            ax.set_ylabel(" ")
            ax.set_xlabel(" ")
        if share_zscale:
            for ax in fig.get_axes():
                ax.get_images()[0].set_clim(vmin, vmax)
        timestamp = self[0, 0].axis_world_coords("time")[-1].iso[slice_index]
        fig.suptitle(f"{self.inventory['instrumentName']} Dataset ({self.inventory['datasetId']}) at time {timestamp} (slice={slice_index})", y=0.95)
        return fig

    @property
    def slice_tiles(self):
        return TiledDatasetSlicer(self._data, self.inventory)

    # TODO: def regrid()

    def __repr__(self):
        """
        Overload the NDData repr because it does not play nice with the dask delayed io.
        """
        prefix = object.__repr__(self)
        return dedent(f"{prefix}\n{self.__str__()}")

    def __str__(self):
        return dataset_info_str(self)
