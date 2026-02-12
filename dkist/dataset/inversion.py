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
    .. warning::

        This class and its functionality are experimental. It may not work as expected and desired features
        may be missing. Bug reports and feature requests can be made to https://github.com/DKISTDC/dkist/issues

    A `~.Dataset`-like container for the raw data used to calculate inversion results.

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
        **kwargs,
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
            Iterable of strings defining which profiles to plot.
            Defaults to 'all'.
        """
        if isinstance(slice_index, (int, slice, types.EllipsisType)):
            slice_index = (slice_index,)

        if figure is None:
            figure = plt.gcf()

        if profiles != "all":
            if isinstance(profiles, str):
                profiles = [profiles]
            selected_profiles = {}
            aligned_axes = {}
            for name in profiles:
                name = name[:name.index("_")] if "_" in name else name
                selected_profiles[name + "_orig"] = self[name + "_orig"]
                selected_profiles[name + "_fit"] = self[name + "_fit"]
                aligned_axes[name + "_orig"] = self.aligned_axes[name + "_orig"]
                aligned_axes[name + "_fit"] = self.aligned_axes[name + "_fit"]
            sliced_profiles = Profiles(
                selected_profiles,
                aligned_axes=tuple(aligned_axes.values()),
            )[slice_index]
        else:
            sliced_profiles = self[slice_index]
            profiles = sliced_profiles.keys()
        lines = []
        for p in profiles:
            line = p[:p.index("_")] if "_" in p else p
            if line not in lines:
                lines.append(line)
        ncols, nrows = len(lines), 4
        gridspec = GridSpec(nrows=nrows, ncols=ncols, figure=figure)
        for l, line in enumerate(lines):
            for s, stokes in enumerate(["I", "Q", "U", "V"]):
                profile = sliced_profiles[line + "_orig"][..., s]
                fit = sliced_profiles[line + "_fit"][..., s]
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
    .. warning::

        This class and its functionality are experimental. It may not work as expected and desired features
        may be missing. Bug reports and feature requests can be made to https://github.com/DKISTDC/dkist/issues

    A `~.Dataset`-like container for level 2 inversion results.

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
        # If the keys are the same then it was a data slice so we should slice the profiles too
        if hasattr(new_inv, "keys") and self.keys() == new_inv.keys():
            # First we need to know which axes are common to the Inversion and the Profiles
            i_ax = self.meta["axes"]
            p_ax = self.profiles.meta["axes"]
            shared_ax = []
            for ax in i_ax:
                if ax in p_ax:
                    shared_ax.append(p_ax.index(ax))
            # Then we construct a new set of slices that reference the correct axes
            # We need a list if only one slice was given
            aslice = [aslice] if isinstance(aslice, (slice, int)) else aslice
            bslice = [aslice[shared_ax[a]] for a in range(min(len(aslice), len(shared_ax)))]
            # Finally slice the Profiles along only the shared axes
            new_inv.profiles = self.profiles[*bslice]
        # If the keys are different then the data is untouched and we can copy the profiles
        else:
            new_inv.profiles = self.profiles
        return new_inv

    def plot(
        self,
        slice_index: int | slice | Iterable[int | slice],
        figure: matplotlib.figure.Figure | None = None,
        inversions: str | Iterable[str] = "all",
        **kwargs,
    ):
        """
        Plot a slice of physical parameters in the Inversion

        Parameters
        ----------
        slice_index
            Object representing a slice which will reduce each component dataset
            of the tileddataset to a 2d image. this is passed to
            `.tileddataset.slice_tiles`, if each tile is already 2d pass ``slice_index=...``.
        figure
            A figure to use for the plot. if not specified the current pyplot
            figure will be used, or a new one created.
        inversions
            Iterable of strings defining which inversions to plot.
            Defaults to 'all'.
        """
        if isinstance(slice_index, (int, slice, types.EllipsisType)):
            slice_index = (slice_index,)

        if figure is None:
            figure = plt.gcf()

        if inversions != "all":
            if isinstance(inversions, str):
                inversions = [inversions]
            sliced_inversions = Inversion(
                {name: self[name] for name in inversions}, aligned_axes="all", profiles=self.profiles
            )[slice_index]
        else:
            sliced_inversions = self[slice_index]
        ncols = len(inversions) if inversions != "all" else 4
        nrows = int(np.ceil(len(sliced_inversions) / ncols))
        gridspec = GridSpec(nrows=nrows, ncols=ncols, figure=figure)
        row = -1
        for i, (name, inv) in enumerate(sliced_inversions.items()):
            if len(inv.shape) not in (1, 2):
                raise ValueError("Slice must reduce inversion data to 1D or 2D")
            col = i % 4
            if col == 0:
                row += 1
            ax_gridspec = gridspec[row, col]
            ax = figure.add_subplot(ax_gridspec, projection=inv)

            inv.plot(axes=ax, **kwargs)

            if col != 0:
                ax.set_ylabel(" ")
            if row != nrows - 1:
                ax.set_xlabel(" ")

            ax.set_title(name)

        return figure
