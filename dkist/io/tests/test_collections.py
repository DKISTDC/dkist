import os

import dask.array as da
import numpy as np
import pytest
from numpy.testing import assert_allclose

import asdf

from dkist.data.test import rootdir
from dkist.io.array_containers import DaskFITSArrayContainer, ExternalArrayReferenceCollection
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
    ac = DaskFITSArrayContainer.from_external_array_references(externalarray, loader=AstropyFITSLoader, basepath=eitdir)
    ext_shape = np.array(externalarray, dtype=object).shape
    assert ac.loader_array.shape == ext_shape
    assert ac.output_shape == tuple(list(ext_shape) + [128, 128])

    array = ac.array.compute()
    assert isinstance(array, np.ndarray)

    ac = ac[5:8]
    ext_shape = np.array(externalarray[5:8], dtype=object).shape
    assert ac.loader_array.shape == ext_shape
    assert ac.output_shape == tuple(list(ext_shape) + [128, 128])

    assert isinstance(ac.array.compute(), np.ndarray)


def test_filenames(externalarray):
    ac = DaskFITSArrayContainer.from_external_array_references(externalarray, loader=AstropyFITSLoader, basepath=eitdir)
    assert len(ac.filenames) == len(externalarray)
    assert ac.filenames == [e.fileuri for e in externalarray]


def test_dask(externalarray):
    ac = DaskFITSArrayContainer.from_external_array_references(externalarray, loader=AstropyFITSLoader, basepath=eitdir)
    ext_shape = np.array(externalarray, dtype=object).shape
    assert ac.loader_array.shape == ext_shape
    assert ac.output_shape == tuple(list(ext_shape) + [128, 128])

    assert isinstance(ac.array, da.Array)
    assert_allclose(ac.array, np.array(ac.array))


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


def test_collection_getitem(tmpdir, earcollection):
    assert isinstance(earcollection[0], ExternalArrayReferenceCollection)
    assert isinstance(earcollection[1], ExternalArrayReferenceCollection)
    assert len(earcollection[0]) == len(earcollection[1]) == 1
    assert earcollection[0:2] == earcollection


def test_basepath_change(externalarray):
    ac = DaskFITSArrayContainer.from_external_array_references(
        externalarray, loader=AstropyFITSLoader)
    array = ac.array
    assert np.isnan(array).all()
    ac.basepath = eitdir
    assert not np.isnan(array).any()


def test_sliced_basepath_change(externalarray):
    ac = DaskFITSArrayContainer.from_external_array_references(
        externalarray, loader=AstropyFITSLoader)
    array = ac.array
    assert np.isnan(array).all()

    sub_array = array[3:4]
    ac.basepath = eitdir
    assert not np.isnan(sub_array).any()
    assert not np.isnan(array).any()
