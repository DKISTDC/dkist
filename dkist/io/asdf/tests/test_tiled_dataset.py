import importlib.resources as importlib_resources
from pathlib import Path

import numpy as np
import pytest

import asdf

from dkist import load_dataset


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
    ds1.save(fname, overwrite=True)

    ds2 = load_dataset(fname)

    assert ds1.shape == ds2.shape
    assert ds1.files.filenames == ds2.files.filenames
    assert ds1.files.shape == ds2.files.shape
    assert (ds1.meta["headers"] == ds2.meta["headers"]).all()
    assert ds1.meta["inventory"] == ds2.meta["inventory"]


@pytest.mark.parametrize("slice", [np.s_[0], np.s_[0, :100, 100:], np.s_[:, :, 0]])
def test_save_tiled_dataset_sliced_tiles(large_tiled_dataset, slice):
    fname = "tds-save-test.asdf"
    ds = large_tiled_dataset

    ds1 = ds.slice_tiles[slice]
    ds1.save(fname, overwrite=True)

    ds2 = load_dataset(fname)

    assert ds1.shape == ds2.shape
    assert ds1.flat.tiles_shape == ds2.flat.tiles_shape
    assert ds1.files.filenames == ds2.files.filenames
    assert ds1.files.shape == ds2.files.shape
    assert (ds1.meta["headers"] == ds2.meta["headers"]).all()
    assert ds1.meta["inventory"] == ds2.meta["inventory"]


def test_save_tiled_dataset_to_existing_file(large_tiled_dataset):
    fname = "tds-overwrite-test.asdf"
    ds = large_tiled_dataset

    ds.save(fname)
    with pytest.raises(FileExistsError):
        ds.save(fname)

    ds1 = ds.slice_tiles[0]
    ds1.save(fname, overwrite=True)

    ds2 = load_dataset(fname)

    # Just need to test enough to make sure it's the sliced ds and not the original in the file
    assert ds1.tiles_shape == ds2.tiles_shape

    # Tidying. I'm sure there's a better fixture-based way to do this
    Path(fname).unlink()
