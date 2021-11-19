import copy

import numpy as np
import pytest

from dkist import Dataset, TiledDataset


def test_tiled_dataset(simple_tiled_dataset, dataset):
    assert isinstance(simple_tiled_dataset, TiledDataset)
    assert simple_tiled_dataset._data[0, 0] in simple_tiled_dataset
    assert 5 not in simple_tiled_dataset
    assert all([isinstance(t, Dataset) for t in simple_tiled_dataset.flat])
    assert all([t.shape == (2,) for t in simple_tiled_dataset])
    assert simple_tiled_dataset.inventory is dataset.meta['inventory']
    assert simple_tiled_dataset.shape == (2, 2)


@pytest.mark.parametrize("aslice", (np.s_[0,0],
                                    np.s_[0],
                                    np.s_[...,0],
                                    np.s_[:,1],
                                    np.s_[1,1],
                                    np.s_[0:2, :]))
def test_tiled_dataset_slice(simple_tiled_dataset, aslice):
    assert np.all(simple_tiled_dataset[aslice] == simple_tiled_dataset._data[aslice])


def test_tiled_dataset_headers(simple_tiled_dataset, dataset):
    assert len(simple_tiled_dataset.combined_headers) == len(dataset.meta['headers']) * 4
    assert simple_tiled_dataset.combined_headers.colnames == dataset.meta['headers'].colnames


def test_tiled_dataset_invalid_construction(dataset, dataset_4d):
    with pytest.raises(ValueError, match="inventory record of the first dataset"):
        TiledDataset(np.array((dataset, dataset_4d)))

    with pytest.raises(ValueError, match="physical types do not match"):
        TiledDataset(np.array((dataset, dataset_4d)), inventory=dataset.meta['inventory'])

    ds2 = copy.deepcopy(dataset)
    ds2.meta['inventory'] = {'hello': 'world'}
    with pytest.raises(ValueError, match="inventory records of all the datasets"):
        TiledDataset(np.array((dataset, ds2)), dataset.meta['inventory'])


def test_tiled_dataset_from_components(dataset):
    shape = (2, 2)
    file_managers = [dataset._file_manager] * 4
    wcses = [dataset.wcs] * 4
    header_tables = [dataset.meta['headers']] * 4
    inventory = dataset.meta['inventory']

    tiled_ds = TiledDataset._from_components(shape, file_managers, wcses, header_tables, inventory)
    assert isinstance(tiled_ds, TiledDataset)
    assert tiled_ds.shape == shape
    assert all([isinstance(t, Dataset) for t in tiled_ds.flat])
    for ds, fm, headers in zip(tiled_ds.flat, file_managers, header_tables):
        assert ds.files == fm
        assert ds.meta['inventory'] is inventory
        assert ds.meta['headers'] is headers
