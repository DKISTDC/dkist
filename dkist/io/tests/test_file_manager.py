from pathlib import Path

import dask.array as da
import numpy as np
import pytest
from numpy.testing import assert_allclose

import asdf

from dkist.data.test import rootdir
from dkist.io.file_manager import SlicedFileManagerProxy

eitdir = Path(rootdir) / 'EIT'


@pytest.fixture
def file_manager(eit_dataset):
    """
    A file manager
    """
    return eit_dataset.files


@pytest.fixture
def externalarray(file_manager):
    """
    An array of external array references.
    """
    return file_manager.external_array_references


def test_load_and_slicing(file_manager, externalarray):
    ext_shape = np.array(externalarray, dtype=object).shape
    assert file_manager._loader_array.shape == ext_shape
    assert file_manager.output_shape == tuple(list(ext_shape) + [128, 128])

    array = file_manager._generate_array().compute()
    assert isinstance(array, np.ndarray)
    # Validate the data is actually loaded from the FITS
    assert not np.isnan(array).all()

    sliced_manager = file_manager[5:8]
    ext_shape = np.array(externalarray[5:8], dtype=object).shape
    assert sliced_manager._loader_array.shape == ext_shape
    assert sliced_manager.output_shape == tuple(list(ext_shape) + [128, 128])


def test_filenames(file_manager, externalarray):
    assert len(file_manager.filenames) == len(externalarray)
    assert file_manager.filenames == [e.fileuri for e in externalarray]


def test_dask(file_manager, externalarray):
    ext_shape = np.array(externalarray, dtype=object).shape
    assert file_manager._loader_array.shape == ext_shape
    assert file_manager.output_shape == tuple(list(ext_shape) + [128, 128])

    assert isinstance(file_manager._generate_array(), da.Array)
    assert_allclose(file_manager._generate_array(), np.array(file_manager._generate_array()))


def test_collection_to_references(tmpdir, file_manager):
    ears = file_manager.external_array_references

    for ear in ears:
        assert isinstance(ear, asdf.ExternalArrayReference)
        assert ear.target == file_manager.target
        assert ear.dtype == file_manager.dtype
        assert ear.shape == file_manager.shape


def test_collection_getitem(tmpdir, file_manager):
    assert isinstance(file_manager[0], SlicedFileManagerProxy)
    assert isinstance(file_manager[1], SlicedFileManagerProxy)
    assert len(file_manager[0]) == len(file_manager[1]) == 1


def test_basepath_change(file_manager):
    file_manager.basepath = None
    array = file_manager._generate_array()
    assert np.isnan(array).all()
    file_manager.basepath = eitdir
    assert not np.isnan(array).any()


def test_sliced_basepath_change(file_manager):
    file_manager.basepath = None
    array = file_manager._generate_array()
    assert np.isnan(array).all()

    sub_array = array[3:4]
    file_manager.basepath = eitdir
    assert not np.isnan(sub_array).any()
    assert not np.isnan(array).any()


def test_file_manager_cube_slice(eit_dataset):
    """
    Slice the cube and then see that the file manager is a new instance sharing the same base path.
    """
    ds = eit_dataset
    assert ds.files is not None

    sds = ds[5:7]

    # Check that we haven't made a copy
    assert ds.files is not sds.files

    # Assert that we have copied the value of basepath
    assert ds.files.basepath == sds.files.basepath

    ## Running sds.download() here would affect the parent cubes data, because
    ## the base paths are the same.

    # If we set a new basepath on the parent cube the sub-cube shouldn't update
    ds.files.basepath = "test1"
    assert ds.files.basepath != sds.files.basepath

    ## Running ds.download() or sds.download() here wouldn't affect the other
    ## one now as the base paths have diverged.

    # Correspondingly changing the base path on the sub cube shouldn't change the parent cube
    sds.files.basepath = "test2"
    assert ds.files.basepath == Path("test1")


def test_file_manager_direct_slice(eit_dataset):
    """
    Assert that slicing the file_manager directly doesn't create a copy.
    """
    ds = eit_dataset
    assert ds.files is not None

    sub_file = ds.files[5]

    # Demonstrate that any operation on a directly sliced file manager also
    # affect the parent object.
    assert sub_file.basepath == ds.files.basepath

    ds.files.basepath = "test1"
    assert sub_file.basepath == ds.files.basepath

    sub_file.basepath = "test2"
    assert sub_file.basepath == ds.files.basepath
