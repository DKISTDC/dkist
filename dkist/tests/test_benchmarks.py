import matplotlib.pyplot as plt
import numpy as np
import pytest

from dkist import load_dataset


@pytest.mark.benchmark
def test_load_asdf(benchmark, large_visp_dataset_file):
    benchmark(load_dataset, large_visp_dataset_file)


@pytest.mark.benchmark
def test_pixel_to_world(benchmark, visp_dataset_no_headers, large_visp_dataset):
    ds = visp_dataset_no_headers
    # pxcoords2 = []
    # for size in ds2.wcs.pixel_shape:
    #     pxcoords2.append(np.arange(size))

    pxcoords = np.mgrid[:ds.wcs.pixel_shape[0]:50,
                        :ds.wcs.pixel_shape[1]:50,
                        :ds.wcs.pixel_shape[2]:50,
                        :ds.wcs.pixel_shape[3]:5]

    benchmark(ds.wcs.pixel_to_world_values, *pxcoords)


@pytest.mark.benchmark
@pytest.mark.parametrize("axes", [
    ["y", None, None, "x"],
])
def test_plot_dataset(benchmark, axes, visp_dataset_no_headers):
    @benchmark
    def plot_and_save_fig(ds=visp_dataset_no_headers, axes=axes):
        ds.plot(plot_axes=axes)
        plt.savefig("tmpplot")
        plt.close()
