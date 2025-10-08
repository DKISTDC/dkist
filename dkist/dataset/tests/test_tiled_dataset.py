import re
import copy
from importlib import resources

import matplotlib.pyplot as plt
import numpy as np
import pytest

import asdf
from astropy.table import Table

from dkist import Dataset, TiledDataset, load_dataset
from dkist.tests.helpers import figure_test
from dkist.utils.exceptions import DKISTUserWarning


def test_tiled_dataset(simple_tiled_dataset, dataset):
    assert isinstance(simple_tiled_dataset, TiledDataset)
    assert simple_tiled_dataset._data[0, 0] in simple_tiled_dataset
    assert 5 not in simple_tiled_dataset
    assert all(t.shape == (2,) for t in simple_tiled_dataset)
    assert simple_tiled_dataset.inventory is dataset.meta["inventory"]
    assert simple_tiled_dataset.shape == (2, 2)


def test_tileddataset_flat(simple_tiled_dataset):
    assert isinstance(simple_tiled_dataset.flat, TiledDataset)
    assert all(isinstance(t, Dataset) for t in simple_tiled_dataset.flat)
    assert not simple_tiled_dataset.flat.mask.all()


@pytest.mark.accept_cli_tiled_dataset
@pytest.mark.parametrize("aslice", [np.s_[0, 0],
                                    np.s_[0],
                                    np.s_[..., 0],
                                    np.s_[:, 1],
                                    np.s_[0, 1],
                                    np.s_[1, 0],
                                    np.s_[0:2, :]])
def test_tiled_dataset_slice(simple_tiled_dataset, aslice):
    if simple_tiled_dataset.mask[aslice].all():
        # If a test case is added where more than one tile is returned
        # here and they are all masked this will probably fail.
        assert simple_tiled_dataset[aslice] is np.ma.masked
    else:
        assert np.all(simple_tiled_dataset[aslice] == simple_tiled_dataset._data[aslice])


def test_tiled_dataset_mask(simple_tiled_dataset):
    assert isinstance(simple_tiled_dataset.mask, np.ndarray)
    new_mask = np.zeros_like(simple_tiled_dataset.mask, dtype=np.bool_)
    simple_tiled_dataset.mask[0, 0] = False
    assert not simple_tiled_dataset.mask[0, 0]

    simple_tiled_dataset.mask = new_mask
    assert not simple_tiled_dataset.mask.any()


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


@pytest.mark.accept_cli_tiled_dataset
def test_tiled_dataset_slice_tiles_headers(large_tiled_dataset):
    sliced = large_tiled_dataset.slice_tiles[0]
    for i, j in np.ndindex(sliced.shape):
        if isinstance(sliced[i, j], np.ma.core.MaskedConstant):
            continue
        assert sliced.shape[1] - j == sliced[i, j].headers["MINDEX1"]
        assert i == sliced[i, j].headers["MINDEX2"] - 1
    m1 = sliced.combined_headers["MINDEX1"]
    m2 = sliced.combined_headers["MINDEX2"]
    # Check that the headers are correctly ordered and sliced during the tile slicing
    # Yes the masking bit here is horrible but we need to ignore headers from tiles that are there but masked out
    expected_m1 = np.ma.MaskedArray(large_tiled_dataset.combined_headers["MINDEX1"][::3],
                                    mask=large_tiled_dataset.mask.flat).compressed()
    expected_m2 = np.ma.MaskedArray(large_tiled_dataset.combined_headers["MINDEX2"][::3],
                                    mask=large_tiled_dataset.mask.flat).compressed()
    assert (m1 == expected_m1).all()
    assert (m2 == expected_m2).all()

def test_tiled_dataset_invalid_construction(dataset, dataset_4d):
    meta = {"inventory": dataset.meta["inventory"]}
    with pytest.raises(ValueError, match="inventory record of the first dataset"):
        TiledDataset(np.array((dataset, dataset_4d)))

    with pytest.raises(ValueError, match="physical types do not match"):
        TiledDataset(np.array((dataset, dataset_4d)), meta=meta)

    ds2 = copy.deepcopy(dataset)
    ds2.meta["inventory"] = {"hello": "world"}
    with pytest.raises(ValueError, match="inventory records of all the datasets"):
        TiledDataset(np.array((dataset, ds2)), meta=meta)


@figure_test
@pytest.mark.remote_data
@pytest.mark.parametrize(("share_zscale", "hide_labels"), [(True, True), (True, False), (False, True), (False, False)],
                         ids=["share_zscale-tick_labels_displayed", "share_zscale-tick_labels_hidden",
                              "independent_zscale-tick_labels_displayed", "independent_zscale-tick_labels_hidden"])
def test_tileddataset_plot(share_zscale, hide_labels):
    from dkist.data.sample import VBI_L1_NZJTB  # noqa: PLC0415
    ori_ds = load_dataset(VBI_L1_NZJTB)

    newtiles = []
    for tile in ori_ds.flat:
        newtiles.append(tile.rebin((1, 8, 8), operation=np.sum))
    # ndcube 2.3.0 introduced a deepcopy for rebin, this broke our dataset validation
    # https://github.com/sunpy/ndcube/issues/815
    for tile in newtiles:
        tile.meta["inventory"] = ori_ds.inventory
    ds = TiledDataset(np.array(newtiles).reshape(ori_ds.shape), meta={"inventory": newtiles[0].inventory})

    fig = plt.figure(figsize=(12, 15))
    with pytest.warns(DKISTUserWarning,
                      match="The metadata ASDF file that produced this dataset is out of date and will result in "
                            "incorrect plots. Please re-download the metadata ASDF file."):
        #TODO: Once sample data have been updated maybe we should test both paths here (old data and new data)
        ds.plot(0, share_zscale=share_zscale, hide_internal_tick_labels=hide_labels, figure=fig)

    return plt.gcf()


@figure_test
@pytest.mark.remote_data
def test_masked_tileddataset_plot():
    from dkist.data.sample import VBI_L1_NZJTB  # noqa: PLC0415
    ds = load_dataset(VBI_L1_NZJTB)
    ds._data.mask[:2, 0] = True
    ds._data.mask[0, 1] = True

    fig = plt.figure(figsize=(12, 15))
    ds.plot(0, figure=fig)
    return fig


@figure_test
@pytest.mark.remote_data
@pytest.mark.parametrize("swap_tile_limits", ["x", "y", "xy", None])
def test_tileddataset_plot_limit_swapping(swap_tile_limits):
    # Also test that row/column sizes are correct

    from dkist.data.sample import VBI_L1_NZJTB  # noqa: PLC0415
    ori_ds = load_dataset(VBI_L1_NZJTB)

    # Swap WCS to make the `swap_tile_limits` option more natural
    for tile in ori_ds.flat:
        tile.wcs.forward_transform[0].cdelt *= -1

    newtiles = []
    for tile in ori_ds.flat:
        newtiles.append(tile.rebin((1, 8, 8), operation=np.sum))
    # ndcube 2.3.0 introduced a deepcopy for rebin, this broke our dataset validation
    # https://github.com/sunpy/ndcube/issues/815
    for tile in newtiles:
        tile.meta["inventory"] = ori_ds.inventory
    ds = TiledDataset(np.array(newtiles).reshape(ori_ds.shape), meta={"inventory": newtiles[0].inventory})

    non_square_ds = ds[:2, :]
    assert non_square_ds.shape[0] != non_square_ds.shape[1]  # Just in case the underlying data change for some reason

    fig = plt.figure(figsize=(12, 15))
    with pytest.warns(DKISTUserWarning,
                      match="The metadata ASDF file that produced this dataset is out of date and will result in "
                            "incorrect plots. Please re-download the metadata ASDF file."):
        #TODO: Once sample data have been updated maybe we should test both paths here (old data and new data)
        non_square_ds.plot(0, share_zscale=False, swap_tile_limits=swap_tile_limits, figure=fig)

    assert fig.axes[0].get_gridspec().get_geometry() == non_square_ds.shape[::-1]
    for ax in fig.axes:
        xlims = ax.get_xlim()
        ylims = ax.get_ylim()

        if swap_tile_limits in ["x", "xy"]:
            assert xlims[0] > xlims[1]
        if swap_tile_limits in ["y", "xy"]:
            assert ylims[0] > ylims[1]
        if swap_tile_limits is None:
            assert xlims[0] < xlims[1]
            assert ylims[0] < ylims[1]

    return plt.gcf()

@pytest.mark.remote_data
def test_tileddataset_plot_non2d_sliceindex():
    from dkist.data.sample import VBI_L1_NZJTB  # noqa: PLC0415
    ds = load_dataset(VBI_L1_NZJTB)

    newtiles = []
    for tile in ds.flat:
        newtiles.append(tile.rebin((1, 8, 8), operation=np.sum))
    # ndcube 2.3.0 introduced a deepcopy for rebin, this broke our dataset validation
    # https://github.com/sunpy/ndcube/issues/815
    for tile in newtiles:
        tile.meta["inventory"] = ds.inventory
    ds = TiledDataset(np.array(newtiles).reshape(ds.shape), meta={"inventory": newtiles[0].inventory})

    already_sliced_ds = ds.slice_tiles[0]

    fig = plt.figure(figsize=(12, 15))
    with pytest.warns(DKISTUserWarning,
                      match="The metadata ASDF file that produced this dataset is out of date and will result in "
                            "incorrect plots. Please re-download the metadata ASDF file."):
        with pytest.raises(ValueError, match=re.escape("Applying slice '(0,)' to this dataset resulted in a 1 "
                "dimensional dataset, you should pass a slice which results in a 2D dataset for each tile.")):
            already_sliced_ds.plot(0, figure=fig)


@pytest.mark.accept_cli_tiled_dataset
def test_repr(simple_tiled_dataset):
    r = repr(simple_tiled_dataset)
    assert str(simple_tiled_dataset[0, 0].data) in r


@pytest.mark.accept_cli_tiled_dataset
def test_tiles_shape(simple_tiled_dataset):
    assert simple_tiled_dataset.tiles_shape == [tuple(tile.data.shape for tile in row) for row in simple_tiled_dataset]


def test_file_manager(large_tiled_dataset):
    ds = large_tiled_dataset
    with pytest.raises(AttributeError):
        ds.files = 10

    assert len(ds.files.filenames) == np.array([len(tile.files.filenames) for tile in ds.flat]).sum()

    # Test slices in various directions
    first_frames = ds.slice_tiles[0]
    assert len(first_frames.files.filenames) == len(first_frames.flat)
    small_mosaic = ds[:2, :2]
    assert len(small_mosaic.files.filenames) == np.array([len(tile.files.filenames) for tile in small_mosaic.flat]).sum()

    ds[1, 1].files.basepath = "/not/a/dir/"
    with pytest.raises(ValueError, match="Not all tiles share the same basepath"):
        ds.files.basepath


@pytest.mark.accept_cli_dataset
def test_broadcast_headers(dataset):
    datasets = np.array([copy.deepcopy(dataset) for _ in range(4)]).reshape([2, 2])
    for i, ds in enumerate(datasets.flat):
        ds.meta["headers"] = Table([[i], [i*10]], names=["spam", "eggs"])
        ds.meta["inventory"] = dataset.meta["inventory"]
    tds = TiledDataset(datasets, meta={"inventory": datasets[0, 0].meta["inventory"], "headers": None})
    assert (tds.combined_headers == Table([[0, 1, 2, 3], [0, 10, 20, 30]], names=["spam", "eggs"])).all()
    tds.meta["headers"]["spam"][0] = 10
    assert tds[0, 0].headers["spam"][0] == 10


@pytest.mark.accept_cli_tiled_dataset
def test_copy_dataset_headers_on_write(tmp_path, large_tiled_dataset):
    with resources.as_file(resources.files("dkist.io") / "level_1_dataset_schema.yaml") as schema_path:
        with asdf.AsdfFile(tree={"dataset": large_tiled_dataset}, custom_schema=schema_path.as_posix()) as afile:
            afile.write_to(tmp_path / "test-header-copies.asdf")
    for ds in large_tiled_dataset.flat:
        assert not isinstance(ds.headers, dict)
