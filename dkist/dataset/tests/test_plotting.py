import numpy as np
import pytest
import matplotlib.pyplot as plt

from astropy.visualization.wcsaxes import WCSAxes

from dkist.dataset.mixins.plotting import ImageAnimatorDataset

# TODO: Move these into a conftest.py
from .test_dataset import array, dataset, dataset_3d, identity_gwcs, identity_gwcs_3d


@pytest.mark.parametrize("aslice", (np.s_[0, :, :], np.s_[:, 0, :], np.s_[:, :, 0]))
def test_dataset_projection(dataset_3d, aslice):
    ds = dataset_3d[aslice]
    ax = plt.subplot(projection=ds)
    assert isinstance(ax, WCSAxes)


def test_non_2d(dataset_3d):
    with pytest.raises(ValueError):
        plt.subplot(projection=dataset_3d)


# @pytest.mark.mpl_image_compare
@pytest.mark.parametrize("aslice", (np.s_[0, :, :], np.s_[:, 0, :], np.s_[:, :, 0]))
def test_2d_plot(dataset_3d, aslice):
    dataset_3d[aslice].plot()
    return plt.gcf()


# @pytest.mark.mpl_image_compare
def test_2d_plot2(dataset_3d):
    dataset_3d[:, :, 0].plot(axes_units=["Angstrom", "deg"])
    return plt.gcf()


@pytest.mark.parametrize(("image_axes", "units"), zip(([-1, -2], [0, 2], [-3, -2]),
                                                      ((None, None), (None, "angstrom"), (None, "angstrom"))))
def test_ia_construct(dataset_3d, image_axes, units):
    # TODO: This seems to work with the SST test dataset
    # from dkist.dataset import Dataset
    # dataset_3d = Dataset.from_directory("/storfa/dkist/generator_data/VTF/SST")[0,0]
    print(dataset_3d)
    a = ImageAnimatorDataset(dataset_3d, image_axes=image_axes, unit_x_axis=units[0], unit_y_axis=units[1])
    return plt.gcf()
