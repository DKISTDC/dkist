import pytest
import matplotlib.pyplot as plt

from .test_dataset import dataset_3d, identity_gwcs_3d, dataset, identity_gwcs, array


@pytest.mark.mpl_image_compare
def test_3d(dataset_3d):
    fig = plt.figure()
    dataset_3d.plot(fig=fig)
    return fig


@pytest.mark.mpl_image_compare
def test_2d(dataset):
    fig = plt.figure()
    dataset.plot()
    return fig


@pytest.mark.mpl_image_compare
def test_3d_hidden(dataset_3d):
    fig = plt.figure()
    dataset_3d._plot_3D_cube(fig=fig)
    return fig


@pytest.mark.mpl_image_compare
def test_2d_hidden(dataset):
    fig = plt.figure()
    dataset._plot_2D_cube()
    return fig
