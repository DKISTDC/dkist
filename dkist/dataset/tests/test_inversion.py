import collections.abc
from itertools import product, permutations

import matplotlib.pyplot as plt
import numpy as np
import pytest

from dkist import Dataset, Inversion, load_dataset
from dkist.dataset.inversion import Profiles
from dkist.tests.helpers import figure_test
from dkist.utils.exceptions import DKISTUserWarning


def test_inversion(inversion):
    assert isinstance(inversion, Inversion)
    assert isinstance(inversion["temperature"], Dataset)
    assert len(inversion) == 11
    assert isinstance(inversion.profiles, Profiles)
    assert len(inversion.profiles.items()) == 6


def test_str(inversion):
    r = repr(inversion)
    keys = "('optical_depth', 'temperature', 'electron_pressure', 'microturbulence', 'mag_strength', 'velocity', 'mag_inclination', 'mag_azimuth', 'geo_height', 'gas_pressure', 'density')"
    assert keys in r
    # Ordering of axes appears to be random causing high chance of test failure
    # Therefore we need to check every possible combination of axis keys
    item0keys = ("time", "custom:pos.helioprojective.lat", "custom:pos.helioprojective.lon")
    item1keys = ("custom:pos.helioprojective.lat", "phys.polarization.stokes", "custom:pos.helioprojective.lon")
    item0_pmtns = list(permutations(item0keys))
    item1_pmtns = list(permutations(item1keys))
    allorders = [str([i0, i1, ("phys.absorption.opticalDepth",)]) for (i0, i1) in product(item0_pmtns, item1_pmtns)]
    assert any([s in r for s in allorders])  # noqa:C419


def test_get_item(inversion):
    sliced_inv = inversion["temperature", "electron_pressure", "velocity"]
    assert isinstance(inversion, Inversion)
    assert len(sliced_inv) == 3
    assert inversion.profiles == sliced_inv.profiles


@pytest.mark.parametrize("slice", [np.s_[100:, 10:20], np.s_[10:], np.s_[0], np.s_[:, :10], np.s_[:, :, :10]])
def test_slice_all(inversion, slice):
    inv = inversion
    sliced_inv = inv[slice]
    ishape = inv["temperature"].data.shape
    pshape = inv.profiles["NaID_orig"].data.shape
    if isinstance(slice, int):
        new_ishape = ishape[1:]
        new_pshape = pshape[1:]
    else:
        if not isinstance(slice, collections.abc.Sequence):
            slice = [slice]
        new_ishape = tuple(
            [((s.stop or n) - (s.start or 0)) // (s.step or 1) for n, s in zip(ishape, slice)]
            + list(ishape[len(slice) :])
        )
        slice = slice[:2]  # Only the first two axes are aligned. May break if we change data
        new_pshape = tuple(
            [((s.stop or n) - (s.start or 0)) // (s.step or 1) for n, s in zip(pshape, slice)]
            + list(pshape[len(slice) :])
        )
    assert sliced_inv["temperature"].data.shape == new_ishape
    assert sliced_inv.profiles["NaID_orig"].data.shape == new_pshape


@figure_test
@pytest.mark.parametrize("inversions", ["all", ["temperature", "electron_pressure", "velocity"], "temperature"])
@pytest.mark.parametrize("slice", [np.s_[0], np.s_[0, 0]])
def test_inversion_plot(inversion, inversions, slice):
    fig = plt.figure(figsize=(12, 18))
    inversion.plot(slice, inversions=inversions)

    return plt.gcf()


@figure_test
@pytest.mark.parametrize("profiles", ["all", ["NaID", "CaII854"], "FeI630"])
def test_profiles_plot(inversion, profiles):
    fig = plt.figure(figsize=(12, 18))
    inversion.profiles.plot(np.s_[0, 0], profiles=profiles)

    return plt.gcf()


def test_inversion_plot_invalid_slice(inversion):
    with pytest.raises(ValueError, match="if you want to slice the NDData object without the WCS, you can remove"):
        inversion.plot(np.s_[0, 0, 0])


def test_profiles_plot_invalid_slice(inversion):
    with pytest.raises(ValueError, match="must reduce profile data to 1D"):
        inversion.profiles.plot(np.s_[0])


@pytest.mark.parametrize("slice_data_first", [True, False])
def test_slice_sliced_inversion(inversion, slice_data_first):
    quants_slice = ("optical_depth", "temperature")
    data_slice = np.s_[100:, 100:]
    inv = inversion
    if slice_data_first:
        inv1 = inv[data_slice]
        inv2 = inv1[quants_slice]
    else:
        inv1 = inv[quants_slice]
        inv2 = inv1[data_slice]
    assert inv["temperature"][data_slice].shape == inv2["temperature"].shape
    assert inv.profiles["NaID_orig"][data_slice].shape == inv2.profiles["NaID_orig"].shape
    assert tuple(inv2.keys()) == quants_slice
    assert inv.profiles.keys() == inv2.profiles.keys()


def test_double_data_slice_inversion(inversion):
    inv = inversion
    inv1 = inv[100:]
    inv2 = inv1[:, 100:]

    assert inv["temperature"][100:, 100:].shape == inv2["temperature"].shape
    assert inv.profiles["NaID_orig"][100:, 100:].shape == inv2.profiles["NaID_orig"].shape
    assert inv.keys() == inv2.keys()
    assert inv.profiles.keys() == inv2.profiles.keys()


def test_slice_inversion_with_mismatched_inversion_wcs(inversion_singleuse):
    inv = inversion_singleuse
    dict.__setitem__(inv, "temperature", inv["temperature"][:100])
    with pytest.raises(DKISTUserWarning, match="datasets in this Inversion do not match the rest"):
        inv1 = inv[100:]


def test_slice_inversion_with_mismatched_profiles_wcs(inversion_singleuse):
    inv = inversion_singleuse
    dict.__setitem__(inv.profiles, "NaID_orig", inv.profiles["NaID_orig"][:100])
    with pytest.raises(DKISTUserWarning, match="datasets in this Profiles do not match the rest"):
        inv1 = inv[100:]


@pytest.mark.parametrize("slice", [np.s_[0], np.s_[0, 0]])
def test_save_inversion_sliced(inversion, slice):
    fname = "inv-save-test.asdf"
    ds = inversion

    ds1 = ds[slice]
    ds1.save(fname, overwrite=True)

    ds2 = load_dataset(fname)

    assert (ds1.aligned_dimensions == ds2.aligned_dimensions).all()
    assert ds1.aligned_axis_physical_types == ds2.aligned_axis_physical_types
    assert ds1.keys() == ds2.keys()
    assert (ds1.meta["headers"] == ds2.meta["headers"]).all()
    assert ds1.meta["inventory"] == ds2.meta["inventory"]


def test_save_inversion_to_existing_file(inversion):
    fname = "inv-overwrite-test.asdf"
    ds = inversion

    ds.save(fname)
    with pytest.raises(FileExistsError):
        ds.save(fname)

    ds1 = ds[0]
    ds1.save(fname, overwrite=True)

    ds2 = load_dataset(fname)

    # Just need to test enough to make sure it's the sliced ds and not the original in the file
    assert ds1.data.shape == ds2.data.shape

    # Tidying. I'm sure there's a better fixture-based way to do this
    Path(fname).unlink()
