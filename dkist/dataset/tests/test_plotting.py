import numpy as np
import pytest
import matplotlib.pyplot as plt

from astropy.visualization.wcsaxes import WCSAxes

# TODO: Move these into a conftest.py
from .test_dataset import array, dataset, dataset_3d, identity_gwcs, identity_gwcs_3d


@pytest.mark.parametrize("aslice", (np.s_[0], np.s_[:, 0, :], np.s_[:, :, 0]))
def test_dataset_projection(dataset_3d, aslice):
    ds = dataset_3d[aslice]
    ax = plt.subplot(projection=ds)
    assert isinstance(ax, WCSAxes)


def test_non_2d(dataset_3d):
    with pytest.raises(ValueError):
        plt.subplot(projection=dataset_3d)


# @pytest.mark.mpl_image_compare
@pytest.mark.parametrize("aslice", (np.s_[0], np.s_[:, 0, :], np.s_[:, :, 0]))
def test_2d_plot(dataset_3d, aslice):
    dataset_3d[aslice].plot()
    return plt.gcf()


# @pytest.mark.mpl_image_compare
def test_2d_plot(dataset_3d):
    dataset_3d[:, :, 0].plot(axes_units=["Angstrom", "deg"])
    return plt.gcf()
