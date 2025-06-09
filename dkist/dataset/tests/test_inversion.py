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
    assert len(inversion.profiles.items()) == 4


def test_str(inversion):
    r = repr(inversion)
    keys = "('opticalDepth', 'temperature', 'electronPressure', 'microTurbulence', 'magStrength', 'velocity', 'magInclination', 'magAzimuth', 'geoHeight', 'gasPressure', 'density')"
    assert keys in r
    aligned = "[('pos.eq.ra', 'pos.eq.dec'), ('pos.eq.ra', 'pos.eq.dec'), ('custom:optical_depth',)]"
    assert aligned in r


def test_get_item(inversion):
    sliced_inv = inversion["temperature", "electronPressure", "velocity"]
    assert isinstance(inversion, Inversion)
    assert len(sliced_inv) == 3
    assert inversion.profiles == sliced_inv.profiles


@figure_test
@pytest.mark.parametrize("inversions", ["all", ["temperature", "electronPressure", "velocity"]])
def test_inversion_plot(inversion, inversions):
    fig = plt.figure(figsize=(12, 18))
    inversion.plot(np.s_[:, :, 0], inversions=inversions)

    return plt.gcf()
