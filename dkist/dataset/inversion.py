import copy
import types
import textwrap
from collections.abc import Iterable

import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

import asdf

from ndcube import NDCollection

from .dataset import Dataset

__all__ = ["Inversion"]


class Profile(NDCollection):
    def plot(
        self,
        slice_index: int | slice | Iterable[int | slice],
        share_zscale: bool = False,
        figure: matplotlib.figure.Figure | None = None,
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
            Determines whether the y-axis scale of the plots should be calculated
            independently (``False``) or shared across all plots (``True``).
            Defaults to False
        figure
            A figure to use for the plot. If not specified the current pyplot
            figure will be used, or a new one created.
        """
        if isinstance(slice_index, (int, slice, types.EllipsisType)):
            slice_index = (slice_index,)

        vmin, vmax = np.inf, 0

        if figure is None:
            figure = plt.gcf()

        sliced_profiles = self[slice_index]
        lines = [k for k in sliced_profiles.keys() if "_fit" not in k]
        ncols, nrows = len(lines), 4
        gridspec = GridSpec(nrows=nrows, ncols=ncols, figure=figure)
        for l, line in enumerate(lines):
            for s, stokes in enumerate(["I", "Q", "U", "V"]):
                profile = sliced_profiles[line][..., s]
                fit = sliced_profiles[line+"_fit"][..., s]

                ax_gridspec = gridspec[s, l]
                ax = figure.add_subplot(ax_gridspec, projection=profile)

                profile.plot(axes=ax, marker="o", linestyle="", **kwargs)
                fit.plot(axes=ax, **kwargs)

                xlabel = ax.get_xlabel()
                ax.set_ylabel(" ")
                ax.set_xlabel(" ")
                if l == 0:
                    ax.set_ylabel(stokes)
                if s == 0:
                    ax.set_title(line)
                if s == 3:
                    ax.set_xlabel(xlabel)

        return figure


class Inversion(NDCollection):
    @classmethod
    def from_test_asdf(cls, asdf_file, *args, **kwargs):
        with asdf.open(asdf_file) as f:
            quants = set(f.tree["inversion"]["quantities"].keys()).difference({"axes", "shape", "wcs"})
            newtree = copy.copy(f.tree)
            for quant in quants:
                raw = f.tree["inversion"]["quantities"][quant]
                fm = raw.pop("data")
                raw["meta"]["inventory"] = {}
                ds = Dataset(**raw, data=fm.dask_array)
                ds._file_manager = fm
                newtree["inversion"]["quantities"][quant] = ds
                # ds.plot(plot_axes=['y', 'x', None])
                # plt.show()

            for profile in ["original", "fit"]:
                for wav in f.tree["inversion"]["profiles"][profile].keys():
                    raw = f.tree["inversion"]["profiles"][profile][wav]
                    fm = raw.pop("data")
                    raw["meta"]["inventory"] = {}
                    shape = fm.dask_array.shape
                    raw["wcs"].array_shape = shape
                    ds = Dataset(**raw, data=fm.dask_array)
                    ds._file_manager = fm
                    newtree["inversion"]["profiles"][profile][wav] = ds
            f.close()

            newtree["inversion"]["quantities"].pop("axes")
            newtree["inversion"]["quantities"].pop("shape")
            newtree["inversion"]["quantities"].pop("wcs")

            newtree["inversion"]["profiles"].pop("axes")
            newtree["inversion"]["profiles"].pop("wcs")
            old_profiles = newtree["inversion"]["profiles"]
            profiles = {}
            for k, v in old_profiles["original"].items():
                profiles[k] = v
            for k, v in old_profiles["fit"].items():
                profiles[k+"_fit"] = v
            profiles = Profile(profiles.items(), aligned_axes=(0, 1, 3))

        return cls(newtree["inversion"]["quantities"].items(), aligned_axes="all", profiles=profiles)

    def __init__(self, *args, profiles=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.profiles = profiles

    def __str__(self):
        quants_repr = "\n".join(super().__str__().split("\n")[2:])
        profiles_repr = "\n".join(self.profiles.__str__().split("\n")[2:])
        s = """\
        Inversion
        ~~~~~~~~~
        {}

        Profiles
        ~~~~~~~~
        {}
        """

        return textwrap.dedent(s).format(quants_repr, profiles_repr)

    def __getitem__(self, aslice):
        new_inv = super().__getitem__(aslice)
        new_inv.profiles = self.profiles

        return new_inv

    def plot(
        self,
        slice_index: int | slice | Iterable[int | slice],
        figure: matplotlib.figure.Figure | None = None,
        inversions: str | Iterable[str] = "all",
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
        figure
            A figure to use for the plot. If not specified the current pyplot
            figure will be used, or a new one created.
        """
        if isinstance(slice_index, (int, slice, types.EllipsisType)):
            slice_index = (slice_index,)

        vmin, vmax = np.inf, 0

        if figure is None:
            figure = plt.gcf()

        sliced_inversions = self[slice_index]
        if inversions != "all":
            sliced_inversions = Inversion({name: self[name] for name in inversions},
                                          aligned_axes="all",
                                          profiles=self.profiles)[slice_index]
        ncols = len(inversions) if inversions != "all" else 4
        nrows = int(np.ceil(len(sliced_inversions) / ncols))
        gridspec = GridSpec(nrows=nrows, ncols=ncols, figure=figure)
        row = -1
        for i, (name, inv) in enumerate(sliced_inversions.items()):
            col = i % 4
            if col == 0:
                row += 1
            ax_gridspec = gridspec[row, col]
            ax = figure.add_subplot(ax_gridspec, projection=inv)

            inv.plot(axes=ax, **kwargs)

            if col != 0:
                ax.set_ylabel(" ")
            if row != nrows-1:
                ax.set_xlabel(" ")

            ax.set_title(name)

        return figure
