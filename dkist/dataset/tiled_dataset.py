"""
Tiled datasets are one dataset which is made up of multiple smaller datasets tiled in space.

A tiled dataset is a "dataset" in terms of how it's provided by the DKIST DC,
but not representable in a single NDCube derived object as the array data are
not contiguous in the spatial dimensions (due to overlaps and offsets).
"""
import os
import types
import warnings
from typing import Any, Self, Literal
from textwrap import dedent
from collections.abc import Iterable, Collection

import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from numpy.typing import NDArray

import astropy
from astropy.table import Table, vstack

from dkist.io.file_manager import DKISTFileManager
from dkist.utils.exceptions import DKISTDeprecationWarning, DKISTUserWarning

from .dataset import Dataset
from .utils import dataset_info_str

__all__ = ["TiledDataset"]


class TiledDatasetFileManager:
    """
    Manage the collection of FITS files backing a `~dkist.TiledDataset`.
    """

    def __init__(self, parent):
        self._parent = parent

    @property
    def basepath(self) -> os.PathLike:
        """
        The path all arrays read data from.
        """
        basepath = self._parent.flat[0].files.basepath
        for tile in self._parent.flat:
            if basepath != tile.files.basepath:
                raise ValueError("Not all tiles share the same basepath. Use 'TiledDataset.files.basepath = <new_path>' to set basepath on all tiles.")
        return basepath

    @basepath.setter
    def basepath(self, basepath: str | os.PathLike):
        for tile in self._parent.flat:
            tile.files.basepath = basepath

    @property
    def filenames(self) -> list[str]:
        return np.array([tile.files.filenames for tile in self._parent.flat]).flatten().tolist()


class TiledDatasetSlicer:
    """
    Basic class to provide the slicing
    """
    def __init__(self, data, meta):
        self.data = data
        self.meta = meta

    def __getitem__(self, slice_):
        new_data = np.zeros_like(self.data.data)

        for i, ds in enumerate(self.data.flat):
            if self.data.mask.flat[i]:
                continue
            new_data.flat[i] = ds[slice_]

        return TiledDataset(new_data, meta=self.meta, mask=self.data.mask)


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

    Parameters
    ----------
    dataset_array
        A numpy object array of Dataset objects. If ``mask=`` is
        provided elements where the mask is `True` will be ignored so
        can be other types, such as `None`.
    mask
        A numpy boolean array, `True` is masked.
    meta
        Associated metadata, the ``"inventory"`` key is used for
        dataset inventory, and is required for download of FITS files
        etc to work.
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
            datasets[i] = Dataset(fm.dask_array, wcs=wcs, meta=meta)
            datasets[i]._file_manager = fm
        datasets = datasets.reshape(shape)

        return cls(datasets, meta={"inventory": inventory})

    def __init__(
        self,
        dataset_array: NDArray[np.object_],
        inventory: dict[Any, Any] | None = None,
        mask: NDArray[np.bool_] | None = None,
        *,
        meta: dict[Any, Any] | None = None
    ):
        if inventory is not None:
            warnings.warn(
                "The inventory= kwarg is deprecated, inventory should be passed as part of the meta argument",
                DKISTDeprecationWarning,
            )
        self._data = np.ma.masked_array(dataset_array, dtype=object, mask=mask)
        meta = meta or {}
        inventory = meta.get("inventory", inventory or {})
        self._validate_component_datasets(self._data, inventory)
        self._meta = meta
        self._meta["inventory"] = inventory
        self._files = DKISTFileManager(TiledDatasetFileManager(parent=self), parent_ndcube=self)

    def __contains__(self, x):
        return any(ele is x for ele in self._data.flat)

    def __len__(self):
        return self._data.__len__()

    def __iter__(self):
        return self._data.__iter__()

    def __getitem__(self, aslice):
        new_data = self._data[aslice]
        if isinstance(new_data, (Dataset, np.ma.core.MaskedConstant)):
            return new_data

        return type(self)(new_data.data, mask=new_data.mask, meta=self.meta)

    @staticmethod
    def _validate_component_datasets(datasets, inventory):
        datasets = [ds for ds in datasets.compressed() if ds is not None]
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
    def mask(self) -> NDArray[np.bool_]:
        """
        The mask for tiles in this dataset.

        An element where the mask is `True` will ignore any dataset in that tile position.
        """
        return self._data.mask

    @mask.setter
    def mask(self, value: NDArray[np.bool_]):
        self._data.mask = value

    @property
    def flat(self) -> Self:
        """
        Represent this `.TiledDataset` as a 1D array.
        """
        return type(self)(self._data.compressed(), meta=self.meta)

    @property
    def meta(self) -> dict[Any, Any]:
        """
        A dictionary of extra metadata about the dataset.
        """
        return self._meta

    @property
    def inventory(self) -> dict[str, Any]:
        """
        The inventory record as kept by the data center for this dataset.
        """
        return self._meta["inventory"]

    @property
    def combined_headers(self) -> Table:
        """
        A single `astropy.table.Table` containing all the FITS headers for all
        files in this dataset.
        """
        return vstack([ds.meta["headers"] for ds in self._data.compressed()])

    @property
    def shape(self) -> tuple[int, int]:
        """
        The shape of the tiled grid.
        """
        return self._data.shape

    @property
    def tiles_shape(self) -> list[tuple[int, ...]]:
        """
        The shape of each individual tile in the TiledDataset.
        """
        return [tuple(tile.data.shape for tile in row) for row in self]

    @staticmethod
    def _get_axislabels(ax):
        if astropy.__version__ >= "6.1.5":
            return (ax.get_xlabel(), ax.get_ylabel())

        xlabel = ylabel = ""
        for coord in ax.coords:
            axislabel_position = coord.axislabels.get_visible_axes()
            if "b" in axislabel_position:
                xlabel = coord.get_axislabel() or coord._get_default_axislabel()
            if "l" in axislabel_position:
                ylabel = coord.get_axislabel() or coord._get_default_axislabel()
        return (xlabel, ylabel)

    def plot(
        self,
        slice_index: int | slice | Iterable[int | slice],
        share_zscale: bool = False,
        figure: matplotlib.figure.Figure | None = None,
        swap_tile_limits: Literal["x", "y", "xy"] | None = None,
        **kwargs
    ):
        """
        Plot a slice of each tile in the TiledDataset

        Parameters
        ----------
        slice_index
            Object representing a slice which will reduce each component dataset
            of the TiledDataset to a 2D image. This is passed to
            `.TiledDataset.slice_tiles`, if each tile is already 2D pass ``slice_index=...``.
        share_zscale
            Determines whether the color scale of the plots should be calculated
            independently (``False``) or shared across all plots (``True``).
            Defaults to False
        figure
            A figure to use for the plot. If not specified the current pyplot
            figure will be used, or a new one created.
        swap_tile_limits
            Invert the axis limits of each tile. Either the "x" or "y" axis limits can be inverted separately, or they
            can both be inverted with "xy". This option is useful if the orientation of the tile data arrays is flipped
            w.r.t. the WCS orientation implied by the mosaic keys. For example, most DL-NIRSP data should be plotted with
            `swap_tile_limits="xy"`.
        """
        if swap_tile_limits not in ["x", "y", "xy", None]:
            raise RuntimeError("swap_tile_limits must be one of ['x', 'y', 'xy', None]")

        if len(self.meta.get("history", {}).get("entries", [])) == 0:
            warnings.warn("The metadata ASDF file that produced this dataset is out of date and "
                          "will result in incorrect plots. Please re-download the metadata ASDF file.",
                          DKISTUserWarning)

        if isinstance(slice_index, (int, slice, types.EllipsisType)):
            slice_index = (slice_index,)

        vmin, vmax = np.inf, 0

        if figure is None:
            figure = plt.gcf()

        sliced_dataset = self.slice_tiles[slice_index]
        # This can change to just .shape once we support ndcube >= 2.3
        if (nd_sliced := len(sliced_dataset.flat[0].data.shape)) != 2:
            raise ValueError(
                f"Applying slice '{slice_index}' to this dataset resulted in a {nd_sliced} "
                "dimensional dataset, you should pass a slice which results in a 2D dataset for each tile."
            )
        dataset_ncols, dataset_nrows = sliced_dataset.shape
        gridspec = GridSpec(nrows=dataset_nrows, ncols=dataset_ncols, figure=figure)
        for col in range(dataset_ncols):
            for row in range(dataset_nrows):
                tile = sliced_dataset[col, row]
                if isinstance(tile, np.ma.core.MaskedConstant):
                    continue

                # Fill up grid from the bottom row
                ax_gridspec = gridspec[dataset_nrows - row - 1, col]
                ax = figure.add_subplot(ax_gridspec, projection=tile.wcs)

                tile.plot(axes=ax, **kwargs)

                if swap_tile_limits in ["x", "xy"]:
                    ax.invert_xaxis()

                if swap_tile_limits in ["y", "xy"]:
                    ax.invert_yaxis()

                ax.set_ylabel(" ")
                ax.set_xlabel(" ")
                if col == row == 0:
                    xlabel, ylabel = self._get_axislabels(ax)
                    figure.supxlabel(xlabel, y=0.05)
                    figure.supylabel(ylabel, x=0.05)

                axmin, axmax = ax.get_images()[0].get_clim()
                vmin = axmin if axmin < vmin else vmin
                vmax = axmax if axmax > vmax else vmax

        if share_zscale:
            for ax in figure.get_axes():
                ax.get_images()[0].set_clim(vmin, vmax)

        title = f"{self.inventory['instrumentName']} Dataset ({self.inventory['datasetId']}) at "
        for i, (coord, val) in enumerate(list(sliced_dataset.flat[0].global_coords.items())[::-1]):
            if coord == "time":
                val = val.iso
            if coord == "stokes":
                val = val.symbol
            title += f"{coord} {val}" + (", " if i != len(slice_index)-1 else " ")
        title += f"(slice={(slice_index if len(slice_index) > 1 else slice_index[0])})".replace("slice(None, None, None)", ":")
        figure.suptitle(title, y=0.95)
        return figure

    @property
    def slice_tiles(self):
        """
        Returns a new TiledDataset with the given slice applied to each of the tiles.

        Examples
        --------
        .. code-block:: python

            >>> from dkist import load_dataset
            >>> from dkist.data.sample import VBI_AJQWW  # doctest: +REMOTE_DATA
            >>> ds = load_dataset(VBI_AJQWW)  # doctest: +REMOTE_DATA
            >>> ds.slice_tiles[0, 10:-10]  # doctest: +REMOTE_DATA
            <dkist.dataset.tiled_dataset.TiledDataset object at ...>
            This VBI Dataset AJQWW is an array of (3, 3) Dataset objects and
            consists of 9 frames.
            Files are stored in ...

            Each Dataset has 2 pixel and 2 world dimensions.

            The data are represented by a <class 'dask.array.core.Array'> object:
            dask.array<getitem, shape=(4076, 4096), dtype=float32, chunksize=(4076, 4096), chunktype=numpy.ndarray>

            Array Dim  Axis Name                  Data size  Bounds
                    0  helioprojective latitude        4076  None
                    1  helioprojective longitude       4096  None

            World Dim  Axis Name                  Physical Type                   Units
                    1  helioprojective latitude   custom:pos.helioprojective.lat  arcsec
                    0  helioprojective longitude  custom:pos.helioprojective.lon  arcsec

            Correlation between pixel and world axes:

                                      |          PIXEL DIMENSIONS
                                      | helioprojective | helioprojective
                     WORLD DIMENSIONS |    longitude    |     latitude
            ------------------------- | --------------- | ---------------
            helioprojective longitude |        x        |        x
             helioprojective latitude |        x        |        x
        """

        return TiledDatasetSlicer(self._data, self.meta)

    # TODO: def regrid()

    def __repr__(self):
        """
        Overload the NDData repr because it does not play nice with the dask delayed io.
        """
        prefix = object.__repr__(self)
        return dedent(f"{prefix}\n{self.__str__()}")

    def __str__(self):
        return dataset_info_str(self)

    @property
    def files(self) -> DKISTFileManager:
        """
        A `~.DKISTFileManager` helper for interacting with the files backing the data in this `.TiledDataset`.
        """
        return self._files
