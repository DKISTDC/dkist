from itertools import product, permutations

import matplotlib.pyplot as plt
import numpy as np
import pytest

from dkist import Dataset, Inversion, load_dataset
from dkist.dataset.inversion import Profiles
from dkist.tests.helpers import figure_test


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


@pytest.mark.parametrize("slice", [np.s_[0]])
def test_save_sliced_inversion(inversion, slice):
    fname = "inv-save-test.asdf"
    inv = inversion

    inv1 = inv[slice]
    inv1.save(fname)

    inv2 = load_dataset(fname)

    assert inv1["temperature"].data.shape == inv2["temperature"].data.shape
    assert inv1["temperature"].files.filenames == inv2["temperature"].files.filenames
    assert inv1["temperature"].files.shape == inv2["temperature"].files.shape
    assert inv1.meta["headers"].keys() == inv2.meta["headers"].keys()
    assert len(inv1.meta["headers"]) == len(inv2.meta["headers"])
    # Time objects apparently compare as False even when they're the same
    inv1.meta["inventory"].pop("created")
    inv2.meta["inventory"].pop("created")
    assert inv1.meta["inventory"] == inv2.meta["inventory"]

    assert inv1.profiles["NaID_orig"].data.shape == inv2.profiles["NaID_orig"].data.shape
    assert inv2.profiles["NaID_orig"].data.shape[:-2] == inv1["temperature"].data.shape[:-1]
