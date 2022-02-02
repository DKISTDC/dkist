from pathlib import Path
from importlib import resources

import numpy as np
import pytest

import asdf
import astropy.table
import gwcs

import dkist
from dkist.data.test import rootdir
from dkist.io import FileManager
from dkist.io.loaders import AstropyFITSLoader

from .helpers import roundtrip_object


@pytest.fixture
def tagobj(request):
    """
    A fixture to lookup other fixtures.
    """
    return request.getfixturevalue(request.param)


@pytest.fixture
def file_manager():
    return FileManager(['test1.fits', 'test2.fits'], 0, 'float', (10, 10),
                       loader=AstropyFITSLoader)


def test_roundtrip_file_manager(file_manager):
    newobj = roundtrip_object(file_manager)
    assert newobj == file_manager


def assert_dataset_equal(new, old):
    old_headers = old.meta.pop("headers")
    new_headers = new.meta.pop("headers")
    assert old_headers.columns == new_headers.columns
    assert len(old_headers) == len(new_headers)
    assert old.meta == new.meta
    old.meta["headers"] = old_headers
    new.meta["headers"] = new_headers
    assert old.wcs.name == new.wcs.name
    assert len(old.wcs.available_frames) == len(new.wcs.available_frames)
    ac_new = new.files.external_array_references
    ac_old = old.files.external_array_references
    assert ac_new == ac_old
    assert old.unit == new.unit
    assert old.mask == new.mask


def test_roundtrip_dataset(dataset):
    newobj = roundtrip_object(dataset)
    assert_dataset_equal(newobj, dataset)


def test_roundtrip_tiled_dataset(simple_tiled_dataset):
    newobj = roundtrip_object(simple_tiled_dataset)

    assert simple_tiled_dataset.inventory == newobj.inventory

    for old_ds, new_ds in zip(simple_tiled_dataset.flat, newobj.flat):
        assert_dataset_equal(new_ds, old_ds)

@pytest.mark.parametrize("tagobj",
                         [
                             "dataset",
                             "simple_tiled_dataset",
                         ],
                         indirect=True)
def test_save_dataset_without_file_schema(tagobj, tmpdir):
    tree = {'dataset': tagobj}
    with asdf.AsdfFile(tree) as afile:
        afile.write_to(Path(tmpdir / "test.asdf"))


@pytest.mark.parametrize("tagobj",
                         [
                             "dataset",
                             "simple_tiled_dataset",
                         ],
                         indirect=True)
def test_save_dataset_with_file_schema(tagobj, tmpdir):
    tree = {'dataset': tagobj}
    with resources.path("dkist.io", "level_1_dataset_schema.yaml") as schema_path:
        with asdf.AsdfFile(tree, custom_schema=schema_path.as_posix()) as afile:
            afile.write_to(Path(tmpdir / "test.asdf"))


@pytest.mark.parametrize("asdf_file",
                         [rootdir / "eit_dataset_0.1.0.asdf",
                          rootdir / "eit_dataset_0.2.0.asdf",
                          rootdir / "eit_dataset_0.3.0.asdf"])
def test_read_all_schema_versions(asdf_file):
    """
    This test validates that we can successfully read a full and valid Dataset
    object from files with all versions of the dataset schema.
    """
    with resources.path("dkist.io", "level_1_dataset_schema.yaml") as schema_path:
        with asdf.open(asdf_file) as afile:
            dataset = afile["dataset"]
            dataset.files.basepath = rootdir / "EIT"

    assert isinstance(dataset, dkist.Dataset)

    # Verify we can load the data
    data = dataset.data.compute()
    assert not np.isnan(data).any()

    assert "inventory" in dataset.meta
    assert "headers" in dataset.meta

    assert isinstance(dataset.meta["headers"], astropy.table.Table)
    assert len(dataset.meta["headers"]) == len(dataset.files.filenames)

    assert isinstance(dataset.wcs, gwcs.WCS)
    assert dataset.wcs.world_n_dim == 3
    assert dataset.wcs.pixel_n_dim == 3
