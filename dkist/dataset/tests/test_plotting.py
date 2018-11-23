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

@pytest.mark.parametrize("aslice", (np.s_[0], np.s_[:, 0, :], np.s_[:, :, 0]))
def test_2d_plot(dataset_3d, aslice):
    dataset_3d[aslice].plot()
    return plt.gcf()

# pytestmark = pytest.mark.skip

# @pytest.mark.mpl_image_compare
# def test_3d(dataset_3d):
#     fig = plt.figure()
#     dataset_3d.plot(fig=fig)
#     return fig

# @pytest.mark.mpl_image_compare
# def test_2d(dataset):
#     fig = plt.figure()
#     dataset.plot()
#     return fig

# @pytest.mark.mpl_image_compare
# def test_3d_hidden(dataset_3d):
#     fig = plt.figure()
#     dataset_3d._plot_3D_cube(fig=fig)
#     return fig

# @pytest.mark.mpl_image_compare
# def test_2d_hidden(dataset):
#     fig = plt.figure()
#     dataset._plot_2D_cube()
#     return fig
