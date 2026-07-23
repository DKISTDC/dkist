import importlib.resources as importlib_resources
from pathlib import Path

import numpy as np
import pytest

import asdf

from dkist import load_dataset, save_dataset
from dkist.utils.exceptions import DKISTUserWarning


def assert_tiled_dataset_equal(new, old, skip_history=False, compare_wcs=True, compare_files=True):
    assert new.shape == old.shape
    assert new.flat.tiles_shape == old.flat.tiles_shape
    assert old.combined_headers.colnames == new.combined_headers.colnames
    assert len(old.combined_headers), len(new.combined_headers)
    old_headers = old.meta.pop("headers")
    new_headers = new.meta.pop("headers")
    assert old_headers.colnames == new_headers.colnames
    assert len(old_headers) == len(new_headers)
    if skip_history:
        old.meta.pop("history")
        new.meta.pop("history")
    assert old.meta == new.meta
    old.meta["headers"] = old_headers
    new.meta["headers"] = new_headers
    if compare_wcs:
        for new_tile, old_tile in zip(new.flat, old.flat):
            assert old_tile.wcs.name == new_tile.wcs.name
            assert len(old_tile.wcs.available_frames) == len(new_tile.wcs.available_frames)
    if compare_files:
        ac_new = new.files.fileuri_array
        ac_old = old.files.fileuri_array
        assert (ac_new.flat == ac_old.flat).all()
    assert (old.mask == new.mask).all()


def test_verify_tiled_dataset_schema(tiled_dataset_asdf_path):
    with importlib_resources.as_file(importlib_resources.files("dkist.io") / "level_1_dataset_schema.yaml"):

        # Firstly verify that the tag versions in the test filename are the ones used in the file
        with asdf.open(tiled_dataset_asdf_path, _force_raw_types=True) as afile:
            assert afile["dataset"]._tag.rsplit("/")[-1] in str(tiled_dataset_asdf_path)
            assert afile["dataset"]["datasets"][0][0]._tag.rsplit("/")[-1] in str(tiled_dataset_asdf_path)


@pytest.mark.parametrize("slice", [np.s_[:2, :2], np.s_[:, 1]])
def test_save_tiled_dataset_sliced(large_tiled_dataset, slice):
    fname = "tds-save-test.asdf"
    ds = large_tiled_dataset

    ds1 = ds[slice]
    save_dataset(ds1, fname, overwrite=True)

    ds2 = load_dataset(fname)

    assert_tiled_dataset_equal(ds2, ds1, skip_history=True)


@pytest.mark.parametrize("slice", [np.s_[0], np.s_[0, :100, 100:], np.s_[:, :, 0]])
def test_save_tiled_dataset_sliced_tiles(large_tiled_dataset, slice):
    fname = "tds-save-test.asdf"
    ds = large_tiled_dataset

    ds1 = ds.slice_tiles[slice]
    save_dataset(ds1, fname, overwrite=True)

    ds2 = load_dataset(fname)

    assert_tiled_dataset_equal(ds2, ds1, skip_history=True, compare_wcs=False)


def test_save_tiled_dataset_to_existing_file(large_tiled_dataset):
    fname = "tds-overwrite-test.asdf"
    ds = large_tiled_dataset

    save_dataset(ds, fname)
    with pytest.raises(FileExistsError):
        save_dataset(ds, fname)

    ds1 = ds.slice_tiles[0]
    save_dataset(ds1, fname, overwrite=True)

    ds2 = load_dataset(fname)

    # Just need to test enough to make sure it's the sliced ds and not the original in the file
    assert ds1.tiles_shape == ds2.tiles_shape

    # Tidying. I'm sure there's a better fixture-based way to do this
    Path(fname).unlink()


@pytest.mark.parametrize("slice", [np.s_[:2, :2], np.s_[:, 1]])
def test_save_tiled_dataset_to_single_file(large_tiled_dataset, slice):
    fname = "tds-single_file-test.asdf"
    ds = large_tiled_dataset[slice]

    save_dataset(ds, fname, overwrite=True, data_format="asdf")

    with pytest.warns(DKISTUserWarning):
        ds1 = load_dataset(fname)

    assert_tiled_dataset_equal(ds1, ds, skip_history=True, compare_files=False)
