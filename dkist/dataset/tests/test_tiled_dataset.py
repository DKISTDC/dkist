import copy

import matplotlib.pyplot as plt
import numpy as np
import pytest

from dkist import Dataset, TiledDataset, load_dataset
from dkist.tests.helpers import figure_test


def test_tiled_dataset(simple_tiled_dataset, dataset):
    assert isinstance(simple_tiled_dataset, TiledDataset)
    assert simple_tiled_dataset._data[0, 0] in simple_tiled_dataset
    assert 5 not in simple_tiled_dataset
    assert all(isinstance(t, Dataset) for t in simple_tiled_dataset.flat)
    assert all(t.shape == (2,) for t in simple_tiled_dataset)
    assert simple_tiled_dataset.inventory is dataset.meta["inventory"]
    assert simple_tiled_dataset.shape == (2, 2)


@pytest.mark.accept_cli_tiled_dataset
@pytest.mark.parametrize("aslice", [np.s_[0,0],
                                    np.s_[0],
                                    np.s_[...,0],
                                    np.s_[:,1],
                                    np.s_[1,1],
                                    np.s_[0:2, :]])
def test_tiled_dataset_slice(simple_tiled_dataset, aslice):
    assert np.all(simple_tiled_dataset[aslice] == simple_tiled_dataset._data[aslice])


@pytest.mark.accept_cli_tiled_dataset
@pytest.mark.parametrize("aslice", [np.s_[0, :100, 100:200]])
def test_tiled_dataset_slice_tiles(large_tiled_dataset, aslice):
    sliced = large_tiled_dataset.slice_tiles[aslice]
    for i, tile in enumerate(sliced.flat):
        # This will throw an AttributeError if you do tile.shape and I don't know why
        assert tile.data.shape == (100, 100)


def test_tiled_dataset_headers(simple_tiled_dataset, dataset):
    assert len(simple_tiled_dataset.combined_headers) == len(dataset.meta["headers"]) * 4
    assert simple_tiled_dataset.combined_headers.colnames == dataset.meta["headers"].colnames


def test_tiled_dataset_invalid_construction(dataset, dataset_4d):
    with pytest.raises(ValueError, match="inventory record of the first dataset"):
        TiledDataset(np.array((dataset, dataset_4d)))

    with pytest.raises(ValueError, match="physical types do not match"):
        TiledDataset(np.array((dataset, dataset_4d)), inventory=dataset.meta["inventory"])

    ds2 = copy.deepcopy(dataset)
    ds2.meta["inventory"] = {"hello": "world"}
    with pytest.raises(ValueError, match="inventory records of all the datasets"):
        TiledDataset(np.array((dataset, ds2)), dataset.meta["inventory"])


def test_tiled_dataset_from_components(dataset):
    shape = (2, 2)
    file_managers = [dataset._file_manager] * 4
    wcses = [dataset.wcs] * 4
    header_tables = [dataset.meta["headers"]] * 4
    inventory = dataset.meta["inventory"]

    tiled_ds = TiledDataset._from_components(shape, file_managers, wcses, header_tables, inventory)
    assert isinstance(tiled_ds, TiledDataset)
    assert tiled_ds.shape == shape
    assert all(isinstance(t, Dataset) for t in tiled_ds.flat)
    for ds, fm, headers in zip(tiled_ds.flat, file_managers, header_tables):
        assert ds.files == fm
        assert ds.meta["inventory"] is inventory
        assert ds.meta["headers"] is headers


@figure_test
@pytest.mark.parametrize("share_zscale", [True, False], ids=["share_zscale", "indpendent_zscale"])
def test_tileddataset_plot(share_zscale):
    from dkist.data.sample import VBI_AJQWW
    ori_ds = load_dataset(VBI_AJQWW)
    newtiles = []
    for tile in ori_ds.flat:
        newtiles.append(tile.rebin((1, 8, 8), operation=np.sum))
    # ndcube 2.3.0 introduced a deepcopy for rebin, this broke our dataset validation
    # https://github.com/sunpy/ndcube/issues/815
    for tile in newtiles:
        tile.meta["inventory"] = ori_ds.inventory
    ds = TiledDataset(np.array(newtiles).reshape(ori_ds.shape), inventory=newtiles[0].inventory)
    fig = plt.figure(figsize=(12, 15))
    ds.plot(0, share_zscale=share_zscale)
    return plt.gcf()


@pytest.mark.accept_cli_tiled_dataset
def test_repr(simple_tiled_dataset):
    r = repr(simple_tiled_dataset)
    assert str(simple_tiled_dataset[0, 0].data) in r


@pytest.mark.accept_cli_tiled_dataset
def test_tiles_shape(simple_tiled_dataset):
    assert simple_tiled_dataset.tiles_shape == [[tile.data.shape for tile in row] for row in simple_tiled_dataset]


def test_file_manager(large_tiled_dataset):
    ds = large_tiled_dataset
    with pytest.raises(AttributeError):
        ds.files = 10

    assert len(ds.files.filenames) == 27
    assert ds.files.shape == (1, 4096, 4096)
    assert ds.files.output_shape == (3, 3, 3, 4096, 4096)

    # Have some slicing tests here
    assert len(ds.slice_tiles[0].files.filenames) == 9
    assert len(ds[:2, :2].files.filenames) == 12

    # TODO Also test that the other checks raise errors
    # This at least demonstrates that the structure works
    ds[1, 1].files.fileuri_array.dtype = np.dtype("<i")
    with pytest.raises(AssertionError, match="must be the same across all tiles"):
        ds.files
