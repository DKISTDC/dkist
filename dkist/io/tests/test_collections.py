import os

import dask.array as da
import numpy as np
import pytest
from numpy.testing import assert_allclose

import asdf

from dkist.data.test import rootdir
from dkist.io import FileManager

eitdir = os.path.join(rootdir, "EIT")


@pytest.fixture
def file_manager():
    """
    A file manager
    """
    with asdf.open(
            os.path.join(eitdir, "eit_test_dataset.asdf")) as f:
        return f.tree['dataset'].file_manager


@pytest.fixture
def externalarray(file_manager):
    """
    An array of external array references.
    """
    return file_manager.external_array_references


def test_slicing(file_manager, externalarray):
    ext_shape = np.array(externalarray, dtype=object).shape
    assert file_manager.loader_array.shape == ext_shape
    assert file_manager.output_shape == tuple(list(ext_shape) + [128, 128])

    array = file_manager.generate_array().compute()
    assert isinstance(array, np.ndarray)

    file_manager = file_manager[5:8]
    ext_shape = np.array(externalarray[5:8], dtype=object).shape
    assert file_manager.loader_array.shape == ext_shape
    assert file_manager.output_shape == tuple(list(ext_shape) + [128, 128])


def test_filenames(file_manager, externalarray):
    assert len(file_manager.filenames) == len(externalarray)
    assert file_manager.filenames == [e.fileuri for e in externalarray]


def test_dask(file_manager, externalarray):
    ext_shape = np.array(externalarray, dtype=object).shape
    assert file_manager.loader_array.shape == ext_shape
    assert file_manager.output_shape == tuple(list(ext_shape) + [128, 128])

    assert isinstance(file_manager.generate_array(), da.Array)
    assert_allclose(file_manager.generate_array(), np.array(file_manager.generate_array()))


def test_collection_to_references(tmpdir, file_manager):
    ears = file_manager.external_array_references

    for ear in ears:
        assert isinstance(ear, asdf.ExternalArrayReference)
        assert ear.target == file_manager.target
        assert ear.dtype == file_manager.dtype
        assert ear.shape == file_manager.shape


def test_collection_getitem(tmpdir, file_manager):
    assert isinstance(file_manager[0], FileManager)
    assert isinstance(file_manager[1], FileManager)
    assert len(file_manager[0]) == len(file_manager[1]) == 1


def test_basepath_change(file_manager):
    file_manager.basepath = None
    array = file_manager.generate_array()
    assert np.isnan(array).all()
    file_manager.basepath = eitdir
    assert not np.isnan(array).any()


def test_sliced_basepath_change(file_manager):
    file_manager.basepath = None
    array = file_manager.generate_array()
    assert np.isnan(array).all()

    sub_array = array[3:4]
    file_manager.basepath = eitdir
    assert not np.isnan(sub_array).any()
    assert not np.isnan(array).any()
