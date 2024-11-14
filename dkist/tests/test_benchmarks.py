import matplotlib.pyplot as plt
import numpy as np
import pytest
from numpy.random import default_rng

import astropy.units as u
from astropy.modeling.models import Tabular1D

from dkist import load_dataset
from dkist.wcs.models import (Ravel, generate_celestial_transform,
                              update_celestial_transform_parameters)


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
def test_plot_dataset(benchmark, axes, visp_dataset_no_headers, tmp_path):
    @benchmark
    def plot_and_save_fig(ds=visp_dataset_no_headers, axes=axes):
        ds.plot(plot_axes=axes)
        plt.savefig(tmp_path / "tmpplot.png")
        plt.close()


@pytest.mark.benchmark
def test_dataset_compute_data_full_files(benchmark):
    """
    Note that although this will load all the files to compute the data, the
    file IO overhead is *not* included in codspeed's timing of the benchmark,
    because it doesn't support that. This test therefore only assesses the
    performance of the compute step.
    """
    from dkist.data.sample import VISP_BKPLX
    ds = load_dataset(VISP_BKPLX)[0, :15]
    benchmark(ds.data.compute)

    assert not np.isnan(ds.data.compute()).any()


@pytest.mark.benchmark
def test_dataset_compute_data_partial_files(benchmark):
    from dkist.data.sample import VISP_BKPLX
    ds = load_dataset(VISP_BKPLX)[0, :15, :100, :100]
    benchmark(ds.data.compute)

    assert not np.isnan(ds.data.compute()).any()


@pytest.mark.benchmark
def test_generate_celestial(benchmark):
    benchmark(generate_celestial_transform,
              crpix=[0, 0] * u.pix,
              crval=[0, 0] * u.arcsec,
              cdelt=[1, 1] * u.arcsec/u.pix,
              pc=np.identity(2) * u.pix,
    )


@pytest.mark.benchmark
def test_update_celestial(benchmark):
    trsfm  = generate_celestial_transform(
              crpix=[0, 0] * u.pix,
              crval=[0, 0] * u.arcsec,
              cdelt=[1, 1] * u.arcsec/u.pix,
              pc=np.identity(2) * u.pix)

    benchmark(update_celestial_transform_parameters,
              trsfm,
              [1, 1] * u.pix,
              [0.5, 0.5] * u.arcsec/u.pix,
              np.identity(2) * u.pix,
              [1, 1] * u.arcsec,
              180 * u.deg,
    )


@pytest.mark.benchmark
def test_raveled_tab1d_model(benchmark):
    ndim = 3
    rng = default_rng()
    array_shape = rng.integers(1, 21, ndim)
    array_bounds = array_shape - 1
    ravel = Ravel(array_shape)
    nelem = np.prod(array_shape)
    units = u.pix
    values = np.arange(nelem) * units
    lut_values = values
    tabular = Tabular1D(
        values,
        lut_values,
        bounds_error=False,
        fill_value=np.nan,
        method="linear",
    )
    raveled_tab = ravel | tabular
    # adding the new axis onto array_bounds makes broadcasting work below
    array_bounds = array_bounds[:, np.newaxis]
    # use 5 as an arbitrary number of inputs
    random_number_shape = len(array_shape), 5
    random_numbers = rng.random(random_number_shape)
    raw_inputs = random_numbers * array_bounds
    inputs = tuple(raw_inputs * units)

    benchmark(raveled_tab, *inputs)


@pytest.mark.benchmark
def test_slice_dataset(benchmark, large_visp_dataset):
    @benchmark
    def slice_dataset(dataset=large_visp_dataset, idx = np.s_[:2, 10:15, 0]):
        sliced = dataset[idx]


@pytest.mark.benchmark
def test_dataset_repr(benchmark, large_visp_dataset):
    benchmark(repr, large_visp_dataset)


@pytest.mark.benchmark
def test_tileddataset_repr(benchmark, simple_tiled_dataset):
    benchmark(repr, simple_tiled_dataset)
