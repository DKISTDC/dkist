import matplotlib.pyplot as plt
import numpy as np
import pytest

from astropy.visualization.wcsaxes import WCSAxes


@pytest.mark.parametrize("aslice", (np.s_[0, :, :], np.s_[:, 0, :], np.s_[:, :, 0]))
def test_dataset_projection(dataset_3d, aslice):
    pytest.importorskip("ndcube", "2.0.2")  # https://github.com/sunpy/ndcube/pull/509
    ds = dataset_3d[aslice]
    ax = plt.subplot(projection=ds)
    assert isinstance(ax, WCSAxes)


# @pytest.mark.mpl_image_compare
@pytest.mark.parametrize("aslice", (np.s_[0, :, :], np.s_[:, 0, :], np.s_[:, :, 0]))
def test_2d_plot(dataset_3d, aslice):
    dataset_3d[aslice].plot()
    return plt.gcf()


# @pytest.mark.mpl_image_compare
def test_2d_plot2(dataset_3d):
    dataset_3d[:, :, 0].plot(axes_units=["Angstrom", "deg", "deg"])
    return plt.gcf()
