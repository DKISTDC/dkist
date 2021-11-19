from pathlib import Path
from importlib import resources

import numpy as np
import pytest

import asdf
import astropy.table
import gwcs
from asdf.tests import helpers

import dkist
from dkist.data.test import rootdir
from dkist.io import FileManager
from dkist.io.loaders import AstropyFITSLoader


@pytest.fixture
def tagobj(request):
    """
    A fixture to lookup other fixtures.
    """
    return request.getfixturevalue(request.param)


@pytest.fixture
def array_container():
    return FileManager(['test1.fits', 'test2.fits'], 0, 'float', (10, 10),
                       loader=AstropyFITSLoader)


@pytest.mark.parametrize("tagobj",
                         [
                             "array_container",
                             "dataset",
                             "simple_tiled_dataset",
                         ],
                         indirect=True)
def test_tags(tagobj, tmpdir):
    tree = {'object': tagobj}
    helpers.assert_roundtrip_tree(tree, tmpdir)


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
