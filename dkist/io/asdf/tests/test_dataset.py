import importlib.resources as importlib_resources
from pathlib import Path

import numpy as np
import pytest

import asdf
import astropy.table
import gwcs
from asdf.testing.helpers import roundtrip_object

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
def file_manager():
    return FileManager.from_parts(["test1.fits", "test2.fits"], 0, "float", (10, 10),
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
    ac_new = new.files.fileuri_array
    ac_old = old.files.fileuri_array
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
def test_save_dataset_without_file_schema(tagobj, tmp_path):
    tree = {"dataset": tagobj}
    with asdf.AsdfFile(tree) as afile:
        afile.write_to(tmp_path / "test.asdf")


def test_asdf_tags(dataset, tmp_path):
    """
    Test the tags and extensions used when saving a dataset.
    """
    tree = {"dataset": dataset}
    with asdf.AsdfFile(tree) as afile:
        afile.write_to(tmp_path / "test.asdf")

    with asdf.open(tmp_path / "test.asdf", _force_raw_types=True) as af:
        assert af.tree["dataset"]._tag == "asdf://dkist.nso.edu/tags/dataset-1.2.0"
        assert af.tree["dataset"]["data"]._tag == "asdf://dkist.nso.edu/tags/file_manager-1.0.0"

        extension_uris = [e.get("extension_uri") for e in af["history"]["extensions"]]
        assert "asdf://dkist.nso.edu/dkist/extensions/dkist-0.9.0" not in extension_uris


@pytest.mark.parametrize("tagobj",
                         [
                             "dataset",
                             "simple_tiled_dataset",
                         ],
                         indirect=True)
def test_save_dataset_with_file_schema(tagobj, tmpdir):
    tree = {"dataset": tagobj}
    with importlib_resources.as_file(importlib_resources.files("dkist.io") / "level_1_dataset_schema.yaml") as schema_path:
        with asdf.AsdfFile(tree, custom_schema=schema_path.as_posix()) as afile:
            afile.write_to(Path(tmpdir / "test.asdf"))


def test_read_all_schema_versions(eit_dataset_asdf_path):
    """
    This test validates that we can successfully read a full and valid Dataset
    object from files with all versions of the dataset schema.
    """
    with importlib_resources.as_file(importlib_resources.files("dkist.io") / "level_1_dataset_schema.yaml"):
        # Firstly verify that the tag versions in the test filename are the ones used in the file
        with asdf.open(eit_dataset_asdf_path, _force_raw_types=True) as afile:
            assert afile["dataset"]._tag.rsplit("/")[-1] in str(eit_dataset_asdf_path)

        with asdf.open(eit_dataset_asdf_path) as afile:
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


@pytest.fixture
def wrap_object(mocker):

    def wrap_object(target, attribute):
        mock = mocker.MagicMock()
        real_attribute = getattr(target, attribute)

        def mocked_attribute(self, *args, **kwargs):
            mock.__call__(*args, **kwargs)
            return real_attribute(self, *args, **kwargs)

        mocker.patch.object(target, attribute, mocked_attribute)

        return mock

    return wrap_object


def test_loader_getitem_with_chunksize(eit_dataset_asdf_path, wrap_object):
    # Import this here to prevent hitting https://bugs.python.org/issue35753 on Python <3.10
    # Importing call is enough to trigger a doctest error
    from unittest.mock import call

    chunksize = (32, 16)
    with asdf.open(eit_dataset_asdf_path) as tree:
        dataset = tree["dataset"]
        dataset.files.basepath = rootdir / "EIT"
        dataset.files._striped_external_array.chunksize = chunksize
        mocked = wrap_object(dataset.files._striped_external_array._loader, "__getitem__")
        dataset._data = dataset.files._generate_array()
        dataset.data.compute()

    expected_call = call((slice(0, chunksize[0], None), slice(0, chunksize[1], None)))
    assert expected_call in mocked.mock_calls


def test_read_wcs_with_backwards_affine():
    """
    This test is a regression test for ASDF files with VCTs in them which were
    written when we incorrectly put the scale before the affine transform in the
    gWCS transforms.
    """
    # This test will only pass with the split axes fix in gwcs
    dataset = dkist.load_dataset(rootdir / "test_old_wcs_BRMQY.asdf")
    wcs = dataset.wcs
    pixel_inputs = [0] * wcs.pixel_n_dim
    world_outputs = wcs.pixel_to_world_values(*pixel_inputs)

    # Assert that our stokes fixing code has worked.
    assert world_outputs[-1] == 1

    # TODO: Requires https://github.com/spacetelescope/gwcs/pull/457
    # if Version(gwcs.__version__) > Version("0.22.dev0"):
    #     pixel_outputs = wcs.world_to_pixel_values(*world_outputs)
    #
    #     assert np.allclose(pixel_inputs, pixel_outputs, atol=1e-6)
