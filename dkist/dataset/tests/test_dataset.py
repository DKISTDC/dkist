from pathlib import Path

import dask.array as da
import numpy as np
import pytest

import asdf
import astropy.units as u
import gwcs
from astropy.table.row import Row
from astropy.tests.helper import assert_quantity_allclose

from dkist.data.test import rootdir
from dkist.dataset import Dataset, TiledDataset, load_dataset
from dkist.io import FileManager
from dkist.utils.exceptions import DKISTDeprecationWarning


@pytest.fixture
def invalid_asdf(tmp_path):
    filename = Path(tmp_path / "test.asdf")
    tree = {"spam": "eggs"}
    with asdf.AsdfFile(tree=tree) as af:
        af.write_to(filename)
    return filename


def test_load_invalid_asdf(invalid_asdf):
    with pytest.raises(TypeError):
        load_dataset(invalid_asdf)


def test_missing_quality(dataset):
    assert dataset.quality_report is None


def test_init_missing_meta_keys(identity_gwcs):
    data = np.zeros(identity_gwcs.array_shape)
    with pytest.raises(ValueError, match=".*must contain the headers table."):
        Dataset(data, wcs=identity_gwcs, meta={"inventory": {}})

    with pytest.raises(ValueError, match=".*must contain the inventory record."):
        Dataset(data, wcs=identity_gwcs, meta={"headers": {}})


@pytest.mark.accept_cli_dataset
def test_repr(dataset, dataset_3d):
    r = repr(dataset)
    assert str(dataset.data) in r
    r = repr(dataset_3d)
    assert str(dataset_3d.data) in r

def test_repr_numpy(dataset):
    # Do it the old way to support old ndcube
    dataset._data = dataset.data.compute()
    r = repr(dataset)
    assert "numpy.ndarray" in r
    assert f"{dataset.data.shape}" in r
    assert f"{dataset.data.dtype}" in r


@pytest.mark.accept_cli_dataset
def test_flat_repr(large_tiled_dataset):
    r = repr(large_tiled_dataset.flat)
    assert f"is an array of ({np.prod(large_tiled_dataset.shape)},) Dataset objects" in r


@pytest.mark.accept_cli_dataset
def test_wcs_roundtrip(dataset):
    p = [1*u.pixel] * dataset.wcs.pixel_n_dim
    w = dataset.wcs.pixel_to_world(*p)
    p2 = dataset.wcs.world_to_pixel(w)
    assert_quantity_allclose(p, p2 * u.pix)


def test_wcs_roundtrip_3d(dataset_3d):
    # TOO generalise this so mark.accept_cli_dataset will work, if possible
    p = (10*u.pixel, 10*u.pixel, 10*u.pixel)
    w = dataset_3d.wcs.pixel_to_world(*p)
    p2 = dataset_3d.wcs.world_to_pixel(*w) * u.pix
    assert_quantity_allclose(p[:2], p2[:2])
    assert_quantity_allclose(p[2], p2[2])


def test_load_from_directory():
    ds = load_dataset(rootdir / "EIT")
    assert isinstance(ds.data, da.Array)
    assert isinstance(ds.wcs, gwcs.WCS)
    assert_quantity_allclose(ds.data.shape, (11, 128, 128))
    assert ds.files.basepath == Path(rootdir / "EIT")


def test_from_directory_no_asdf(tmp_path):
    with pytest.raises(ValueError, match="No asdf file found"):
        load_dataset(tmp_path)


def test_from_not_directory():
    with pytest.raises(ValueError, match="does not exist"):
        load_dataset(rootdir / "notadirectory")


def test_load_tiled_dataset():
    ds = load_dataset(rootdir / "test_tiled_dataset-1.0.0_dataset-1.1.0.asdf")
    assert isinstance(ds, TiledDataset)
    assert ds.shape == (3, 3)


def test_load_with_old_methods():
    with pytest.warns(DKISTDeprecationWarning):
        ds = Dataset.from_directory(rootdir / "EIT")
        assert isinstance(ds.data, da.Array)
        assert isinstance(ds.wcs, gwcs.WCS)
        assert_quantity_allclose(ds.data.shape, (11, 128, 128))
        assert ds.files.basepath == Path(rootdir / "EIT")

    with pytest.warns(DKISTDeprecationWarning):
        ds = Dataset.from_asdf(rootdir / "EIT" / "eit_test_dataset.asdf")
        assert isinstance(ds.data, da.Array)
        assert isinstance(ds.wcs, gwcs.WCS)
        assert_quantity_allclose(ds.data.shape, (11, 128, 128))
        assert ds.files.basepath == Path(rootdir / "EIT")


def test_from_directory_not_dir():
    with pytest.raises(ValueError, match="asdf does not exist"):
        load_dataset(rootdir / "EIT" / "eit_2004-03-01T00_00_10.515000.asdf")


def test_load_with_invalid_input():
    with pytest.raises(TypeError, match="Input type .* not recognised."):
        load_dataset(42)


def test_crop_few_slices(dataset_4d):
    sds = dataset_4d[0, 0]
    assert sds.wcs.world_n_dim == 2


def test_file_manager():
    dataset = load_dataset(rootdir / "EIT")
    assert dataset.files is dataset._file_manager
    with pytest.raises(AttributeError):
        dataset.files = 10

    assert len(dataset.files.filenames) == 11

    assert isinstance(dataset[5]._file_manager, FileManager)
    assert len(dataset[..., 5].files.filenames) == 11
    assert len(dataset[5].files.filenames) == 1


def test_no_file_manager(dataset_3d):
    assert dataset_3d.files is None


def test_inventory_propery():
    dataset = load_dataset(rootdir / "EIT")
    assert dataset.inventory == dataset.meta["inventory"]


def test_header_slicing_single_index():
    dataset = load_dataset(rootdir / "EIT")
    idx = 5
    sliced = dataset[idx]

    sliced_headers = dataset.headers[idx]
    # Filenames in the header don't match the names of the files because why would you expect those things to be the same
    sliced_header_files = sliced_headers["FILENAME"] + "_s.fits"

    assert len(sliced.files.filenames) == 1
    assert isinstance(sliced_headers, Row)
    assert sliced.files.filenames[0] == sliced_header_files
    assert (sliced.headers["DINDEX3"] == sliced_headers["DINDEX3"]).all()


@pytest.mark.accept_cli_dataset
def test_header_slicing_3D_slice(large_visp_dataset):
    dataset = large_visp_dataset
    idx = np.s_[:2, 10:15, 0]
    sliced = dataset[idx]

    file_idx = dataset.files._array_slice_to_loader_slice(idx)
    grid = np.mgrid[{tuple: file_idx, slice: (file_idx,)}[type(file_idx)]]
    file_idx = tuple(grid[i].ravel() for i in range(np.prod(grid.shape[:-2])))

    flat_idx = np.ravel_multi_index(file_idx, dataset.data.shape[:-2])

    sliced_headers = dataset.headers[flat_idx]

    assert len(sliced.files.filenames) == len(sliced_headers["FILENAME"]) == len(sliced.headers)
    assert (sliced.headers["DINDEX3", "DINDEX4"] == sliced_headers["DINDEX3", "DINDEX4"]).all()


@pytest.mark.accept_cli_dataset
def test_file_slicing_with_dummy_axis(dataset_5d_dummy_filemanager_axis):
    ds = dataset_5d_dummy_filemanager_axis
    shape = ds.data.shape
    assert len(ds.files) == np.prod(shape[:3])
    assert len(ds[0].files) == np.prod(shape[1:3])
    assert len(ds[0, 0].files) == np.prod(shape[2])
    assert len(ds[0, 0, 0].files) == 1
    assert len(ds[0, 0, 0, 0].files) == 1


@pytest.mark.accept_cli_dataset
def test_file_slicing_without_dummy_axis(dataset_5d):
    ds = dataset_5d
    shape = ds.data.shape
    assert len(ds.files) == np.prod(shape[:3])
    assert len(ds[0].files) == np.prod(shape[1:3])
    assert len(ds[0, 0].files) == np.prod(shape[2])
    assert len(ds[0, 0, 0].files) == 1
    assert len(ds[0, 0, 0, 0].files) == 1
