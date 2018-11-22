import pytest
import matplotlib.pyplot as plt

# TODO: Move these into a conftest.py
from .test_dataset import array, dataset, dataset_3d, identity_gwcs, identity_gwcs_3d


def test_coord_meta(dataset_3d):
    ds = dataset_3d[:, :, 0]
    print(ds._make_coord_meta())
    assert False


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
