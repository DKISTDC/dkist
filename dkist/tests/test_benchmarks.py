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


@pytest.mark.benchmark(min_rounds=1)
@pytest.mark.parametrize("axes", [
    [None, "y", "x", None],
])
def test_plot_dataset(benchmark, axes, visp_dataset_no_headers):
    @benchmark
    def plot_and_save_fig(ds=visp_dataset_no_headers, axes=axes):
        ds.plot(plot_axes=axes)
        plt.savefig("tmpplot")
        plt.close()
