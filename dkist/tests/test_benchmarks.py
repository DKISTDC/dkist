import matplotlib.pyplot as plt
import numpy as np
import pytest

from dkist import load_dataset


@pytest.mark.benchmark
def test_load_asdf(benchmark, large_visp_dataset_file):
    benchmark(load_dataset, large_visp_dataset_file)


@pytest.mark.benchmark
def test_pixel_to_world(benchmark, large_visp_dataset):
    ds = large_visp_dataset
    pxcoords = []
    for size in ds.wcs.pixel_shape:
        pxcoords.append(np.arange(size))

    pxcoords = np.mgrid[:ds.wcs.pixel_shape[0]:5,
                        :ds.wcs.pixel_shape[1]:5,
                        :ds.wcs.pixel_shape[2]:5]

    benchmark(ds.wcs.pixel_to_world_values, *pxcoords, 0)


@pytest.mark.benchmark(min_rounds=2)
@pytest.mark.parametrize("axes", [
    ["y", "x", None, None],
    ["y", None, "x", None],
    ["y", None, None, "x"],
    [None, "y", "x", None],
    [None, "y", None, "x"],
    [None, None, "y", "x"],
])
def test_plot_dataset(benchmark, axes, large_visp_dataset):
    @benchmark
    def plot_and_save_fig(ds=large_visp_dataset, axes=axes):
        ds.plot(plot_axes=axes)
    plt.close()
