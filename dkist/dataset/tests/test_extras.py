import dask.array as da
import numpy as np

from astropy.io import fits
from astropy.table import Table


def test_name(dataset_extra_obj):
    assert dataset_extra_obj.name == "test_extra"


def test_headers(dataset_extra_obj):
    assert isinstance(dataset_extra_obj.headers, Table)
    assert len(dataset_extra_obj.headers) == 2
    assert dataset_extra_obj.headers.colnames == ["col1", "col2"]


def test_data(dataset_extra_obj, dataset_extra_dir):
    data = dataset_extra_obj.data
    assert isinstance(data, list)
    assert len(data) == 2
    for ear, arr in zip(dataset_extra_obj._ears, data):
        assert isinstance(arr, da.Array)
        assert arr.shape == (10, 10)
        dask_arr = arr.compute()
        fits_arr = fits.getdata(dataset_extra_dir / ear.fileuri, hdu=ear.target)
        np.testing.assert_allclose(dask_arr, fits_arr)
