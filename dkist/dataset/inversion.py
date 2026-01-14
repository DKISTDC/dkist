import types
import textwrap
from collections.abc import Iterable

import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

from ndcube import NDCollection

__all__ = ["Inversion", "Profiles"]


class Profiles(NDCollection):
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
        lines = {k[:k.index("_")] for k in sliced_profiles.keys()}
        ncols, nrows = len(lines), 4
        gridspec = GridSpec(nrows=nrows, ncols=ncols, figure=figure)
        for l, line in enumerate(lines):
            for s, stokes in enumerate(["I", "Q", "U", "V"]):
                profile = sliced_profiles[line+"_orig"][..., s]
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
