import os

import numpy as np
import pytest
import dask.array as da
from numpy.testing import assert_allclose

import asdf

from dkist.io.fits import AstropyFITSLoader
from dkist.data.test import rootdir
from dkist.io.reference_collections import DaskFITSArrayContainer, NumpyFITSArrayContainer

eitdir = os.path.join(rootdir, "EIT")


@pytest.fixture
def externalarray():
    """
    An array of external array references.
    """
    with asdf.AsdfFile.open(
            os.path.join(eitdir,
                         "eit_2004-03-01T00:00:10.515000.asdf")) as f:
        return f.tree['dataset']


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
