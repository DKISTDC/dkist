import os

import dask.array as da
import numpy as np
import pytest
from numpy.testing import assert_allclose

import asdf

from dkist.data.test import rootdir
from dkist.io.array_containers import DaskFITSArrayContainer, NumpyFITSArrayContainer
from dkist.io.fits import AstropyFITSLoader

eitdir = os.path.join(rootdir, "EIT")


@pytest.fixture
def externalarray():
    """
    An array of external array references.
    """
    with asdf.AsdfFile.open(
            os.path.join(eitdir, "eit_test_dataset.asdf")) as f:
        return f.tree['dataset']._array_container.as_external_array_references()


def test_slicing(externalarray):
    ac = NumpyFITSArrayContainer(externalarray, loader=AstropyFITSLoader, basepath=eitdir)
    ext_shape = np.array(externalarray, dtype=object).shape
    assert ac.loader_array.shape == ext_shape
    assert ac.shape == tuple(list(ext_shape) + [128, 128])

    assert isinstance(ac.array, np.ndarray)
    assert_allclose(ac.array, np.array(ac))

    ac = ac[5:8]
    ext_shape = np.array(externalarray[5:8], dtype=object).shape
    assert ac.loader_array.shape == ext_shape
    assert ac.shape == tuple(list(ext_shape) + [128, 128])

    assert isinstance(ac.array, np.ndarray)
    assert_allclose(ac.array, np.array(ac))


def test_filenames(externalarray):
    ac = NumpyFITSArrayContainer(externalarray, loader=AstropyFITSLoader, basepath=eitdir)
    assert len(ac.filenames) == len(externalarray)
    assert ac.filenames == [e.fileuri for e in externalarray]


def test_numpy(externalarray):
    ac = NumpyFITSArrayContainer(externalarray, loader=AstropyFITSLoader, basepath=eitdir)
    ext_shape = np.array(externalarray, dtype=object).shape
    assert ac.loader_array.shape == ext_shape
    assert ac.shape == tuple(list(ext_shape) + [128, 128])

    assert isinstance(ac.array, np.ndarray)
    assert_allclose(ac.array, np.array(ac))


def test_dask(externalarray):
    ac = DaskFITSArrayContainer(externalarray, loader=AstropyFITSLoader, basepath=eitdir)
    ext_shape = np.array(externalarray, dtype=object).shape
    assert ac.loader_array.shape == ext_shape
    assert ac.shape == tuple(list(ext_shape) + [128, 128])

    assert isinstance(ac.array, da.Array)
    assert_allclose(ac.array, np.array(ac.array))
