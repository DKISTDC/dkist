import matplotlib.pyplot as plt
import numpy as np
import pytest

from dkist import load_dataset


@pytest.mark.benchmark
def test_load_asdf(benchmark, large_visp_dataset_file):
    benchmark(load_dataset, large_visp_dataset_file)


@pytest.mark.benchmark
def test_pixel_to_world(benchmark, visp_dataset_no_headers):
    ds = visp_dataset_no_headers

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


@pytest.mark.benchmark
def test_dataset_compute_data_full_files(benchmark, real_visp):
    """
    Note that although this will load all the files to compute the data, the
    file IO overhead is *not* included in codspeed's timing of the benchmark,
    because it doesn't support that. This test therefore only assesses the
    performance of the compute step.
    """
    ds = real_visp[0, :15]
    benchmark(ds.data.compute)

    assert not np.isnan(ds.data.compute()).any()


@pytest.mark.benchmark
def test_dataset_compute_data_partial_files(benchmark, real_visp):
    ds = real_visp[0, :15, :100, :100]
    benchmark(ds.data.compute)

    assert not np.isnan(ds.data.compute()).any()
