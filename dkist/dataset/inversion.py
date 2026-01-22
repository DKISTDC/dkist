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
    """
    A `~Dataset`-like container for the raw data used to calculate inversion results.

    Parameters
    ----------
    key_data_pairs: `dict` or sequence of `tuple` of (`str`, `~ndcube.NDCube` or `~ndcube.NDCubeSequence`)
        Names and data cubes/sequences to hold in the collection.

    aligned_axes: `tuple` of `int`, `tuple` of `tuple` of `int`, 'all', or None, optional
        Axes of each cube/sequence that are aligned in numpy order.
        See `~ndcube.NDCollection` for more detail.

    meta: `dict`, optional
        General metadata for the overall collection.
    """
    def plot(
        self,
        slice_index: int | slice | Iterable[int | slice],
        figure: matplotlib.figure.Figure | None = None,
        profiles: str | Iterable[str] = "all",
        **kwargs
    ):
        """
        Plot a single original spectrum and its fit from each of some number of profiles in the Profiles object

        Parameters
        ----------
        slice_index
            Object representing a slice which will reduce each component dataset
            of the TiledDataset to a 2D image. This is passed to
            `.TiledDataset.slice_tiles`, if each tile is already 2D pass ``slice_index=...``.
        figure
            A figure to use for the plot. If not specified the current pyplot
            figure will be used, or a new one created.
        profiles
            iterable of strings defining which profiles to plot.
            defaults to 'all'.
        """
        if isinstance(slice_index, (int, slice, types.EllipsisType)):
            slice_index = (slice_index,)

        if figure is None:
            figure = plt.gcf()

        if profiles != "all":
            sliced_profiles = Profiles({name: self[name] for name in profiles},
                                       aligned_axes="all")[slice_index]
        else:
            sliced_profiles = self[slice_index]
        lines = {k[:k.index("_")] for k in sliced_profiles.keys()}
        ncols, nrows = len(lines), 4
        gridspec = GridSpec(nrows=nrows, ncols=ncols, figure=figure)
        for l, line in enumerate(lines):
            for s, stokes in enumerate(["I", "Q", "U", "V"]):
                profile = sliced_profiles[line+"_orig"][..., s]
                fit = sliced_profiles[line+"_fit"][..., s]
                if len(profile.shape) != 1:
                    raise ValueError("Slice must reduce profile data to 1D")

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
    """
    A `~Dataset`-like container for level 2 inversion results.

    Parameters
    ----------
    key_data_pairs: `dict` or sequence of `tuple` of (`str`, `~ndcube.NDCube` or `~ndcube.NDCubeSequence`)
        Names and data cubes/sequences to hold in the collection.

    aligned_axes: `tuple` of `int`, `tuple` of `tuple` of `int`, 'all', or None, optional
        Axes of each cube/sequence that are aligned in numpy order.
        See `~ndcube.NDCollection` for more detail.

    meta: `dict`, optional
        General metadata for the overall collection.
    """
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
        Plot a slice of physical parameters in the Inversion

        Parameters
        ----------
        slice_index
            object representing a slice which will reduce each component dataset
            of the tileddataset to a 2d image. this is passed to
            `.tileddataset.slice_tiles`, if each tile is already 2d pass ``slice_index=...``.
        figure
            a figure to use for the plot. if not specified the current pyplot
            figure will be used, or a new one created.
        inversions
            iterable of strings defining which inversions to plot.
            defaults to 'all'.
        """
        if isinstance(slice_index, (int, slice, types.EllipsisType)):
            slice_index = (slice_index,)

        if figure is None:
            figure = plt.gcf()

        if inversions != "all":
            sliced_inversions = Inversion({name: self[name] for name in inversions},
                                          aligned_axes="all",
                                          profiles=self.profiles)[slice_index]
        else:
            sliced_inversions = self[slice_index]
        ncols = len(inversions) if inversions != "all" else 4
        nrows = int(np.ceil(len(sliced_inversions) / ncols))
        gridspec = GridSpec(nrows=nrows, ncols=ncols, figure=figure)
        row = -1
        for i, (name, inv) in enumerate(sliced_inversions.items()):
            if len(inv.shape) != 2:
                raise ValueError("Slice must reduce inversion data to 2D")
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
