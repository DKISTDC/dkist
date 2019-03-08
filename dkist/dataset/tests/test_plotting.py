import matplotlib.pyplot as plt
import numpy as np
import pytest

from astropy.visualization.wcsaxes import WCSAxes

from dkist.dataset.mixins.plotting import ImageAnimatorDataset


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


# @pytest.mark.mpl_image_compare
@pytest.mark.xfail
@pytest.mark.parametrize(("image_axes", "units"), zip(([-1, -2], [0, 2], [-3, -2]),
                                                      ((None, None),
                                                       ("angstrom", None), ("angstrom", None))))
def test_ia_construct(dataset_3d, image_axes, units):
    # TODO:
    # I am not sure what's going on here, it looks like the sunpy imageanimator
    # thing is just completely wonkey. Probably best to test this with the
    # actual SST dataset and try and make some real plots to see what's
    # actually broken.
    a = ImageAnimatorDataset(dataset_3d, image_axes=image_axes, unit_x_axis=units[0], unit_y_axis=units[1])
    return plt.gcf()
