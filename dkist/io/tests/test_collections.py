import os

import dask.array as da
import numpy as np
import pytest
from numpy.testing import assert_allclose

import asdf

from dkist.data.test import rootdir
from dkist.io.array_containers import (DaskFITSArrayCollection, ExternalArrayReferenceCollection,
                                       NumpyFITSArrayCollection)
from dkist.io.loaders import AstropyFITSLoader

eitdir = os.path.join(rootdir, "EIT")


@pytest.fixture
def externalarray():
    """
    An array of external array references.
    """
    with asdf.open(
            os.path.join(eitdir, "eit_test_dataset.asdf")) as f:
        return f.tree['dataset']._array_container.external_array_references


def test_slicing(externalarray):
    ac = NumpyFITSArrayCollection.from_external_array_references(externalarray, loader=AstropyFITSLoader, basepath=eitdir)
    ext_shape = np.array(externalarray, dtype=object).shape
    assert ac.loader_array.shape == ext_shape
    assert ac.get_output_shape() == tuple(list(ext_shape) + [128, 128])

    assert isinstance(ac.get_array(), np.ndarray)

    assert isinstance(ac.get_array(np.s_[5:8]), np.ndarray)


def test_filenames(externalarray):
    ac = NumpyFITSArrayCollection.from_external_array_references(externalarray, loader=AstropyFITSLoader, basepath=eitdir)
    assert len(ac.get_filenames()) == len(externalarray)
    assert ac.get_filenames() == [e.fileuri for e in externalarray]


def test_numpy(externalarray):
    ac = NumpyFITSArrayCollection.from_external_array_references(externalarray, loader=AstropyFITSLoader, basepath=eitdir)
    ext_shape = np.array(externalarray, dtype=object).shape
    assert ac.loader_array.shape == ext_shape
    assert ac.get_output_shape() == tuple(list(ext_shape) + [128, 128])

    assert isinstance(ac.get_array(), np.ndarray)


def test_dask(externalarray):
    ac = DaskFITSArrayCollection.from_external_array_references(externalarray, loader=AstropyFITSLoader, basepath=eitdir)
    ext_shape = np.array(externalarray, dtype=object).shape
    assert ac.loader_array.shape == ext_shape
    assert ac.get_output_shape() == tuple(list(ext_shape) + [128, 128])

    assert isinstance(ac.get_array(), da.Array)


@pytest.fixture
def earcollection():
    return ExternalArrayReferenceCollection(["./nonexistant.fits",
                                             "./nonexistant-1.fits"],
                                             1,
                                             "np.float64",
                                             (100, 100))


def test_collection_to_references(tmpdir, earcollection):
    ears = earcollection.external_array_references
    assert len(earcollection) == len(ears) == 2

    for ear in ears:
        assert isinstance(ear, asdf.ExternalArrayReference)
        assert ear.target == earcollection.target
        assert ear.dtype == earcollection.dtype
        assert ear.shape == earcollection.shape

def _make_collection_with_shape(file_shape, array_shape):
    uris = np.zeros(file_shape, dtype=str).tolist()
    target = 0
    dtype = np.float32
    shape = array_shape
    return NumpyFITSArrayCollection(uris, target, dtype, shape, loader=AstropyFITSLoader)

# def test_slice_conversion():
#     ac = _make_collection_with_shape((5, 6), (1, 10, 10))
#     assert ac.array_slice_to_reference_slice(np.s_[:, 3:4]) == (slice(None), slice(None))
#     assert ac.array_slice_to_reference_slice(np.s_[:]) == (slice(None), slice(None))
#     assert ac.array_slice_to_reference_slice(np.s_[3, :]) == (3, slice(None))

#     ac = _make_collection_with_shape((5, 6), (10, 10))
#     assert ac.array_slice_to_reference_slice(np.s_[2, 4, :]) == (slice(None), slice(None))
#     assert ac.array_slice_to_reference_slice(np.s_[:]) == (slice(None), slice(None))
#     assert ac.array_slice_to_reference_slice(np.s_[:, :, 3, :]) == (3, slice(None))
