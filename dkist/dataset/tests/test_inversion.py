from itertools import product, permutations

import matplotlib.pyplot as plt
import numpy as np
import pytest

from dkist import Dataset, Inversion
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
    assert any([s in r for s in allorders])  #noqa:C419


def test_get_item(inversion):
    sliced_inv = inversion["temperature", "electron_pressure", "velocity"]
    assert isinstance(inversion, Inversion)
    assert len(sliced_inv) == 3
    assert inversion.profiles == sliced_inv.profiles


@figure_test
@pytest.mark.parametrize("inversions", ["all", ["temperature", "electron_pressure", "velocity"]])
def test_inversion_plot(inversion, inversions):
    fig = plt.figure(figsize=(12, 18))
    inversion.plot(np.s_[0], inversions=inversions)

    return plt.gcf()


@figure_test
@pytest.mark.parametrize("profiles", ["all", ["NaID", "CaII854"]])
def test_profiles_plot(inversion, profiles):
    fig = plt.figure(figsize=(12, 18))
    inversion.profiles.plot(np.s_[0, 0], profiles=profiles)

    return plt.gcf()


def test_inversion_plot_invalid_slice(inversion):
    with pytest.raises(ValueError, match="must reduce inversion data to 2D"):
        inversion.plot(np.s_[0, 0])


def test_profiles_plot_invalid_slice(inversion):
    with pytest.raises(ValueError, match="must reduce profile data to 1D"):
        inversion.profiles.plot(np.s_[0])
