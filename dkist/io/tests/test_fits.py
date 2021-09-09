from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_allclose

import asdf

from dkist.data.test import rootdir
from dkist.io.file_manager import FileManager
from dkist.io.loaders import AstropyFITSLoader

eitdir = Path(rootdir) / 'EIT'


@pytest.fixture
def relative_ear():
    return asdf.ExternalArrayReference("efz20040301.000010_s.fits",
                                       0,
                                       "float64",
                                       (128, 128))


@pytest.fixture
def absolute_ear():
    return asdf.ExternalArrayReference(eitdir / "efz20040301.000010_s.fits",
                                       0,
                                       "float64",
                                       (128, 128))

@pytest.fixture
def relative_ac(relative_ear):
    return FileManager([relative_ear.fileuri],
                       relative_ear.target,
                       relative_ear.dtype,
                       relative_ear.shape,
                       loader=AstropyFITSLoader,
                       basepath=eitdir)


@pytest.fixture
def relative_fl(relative_ac):
    return relative_ac._loader_array.flat[0]


@pytest.fixture
def absolute_ac(absolute_ear):
    return FileManager([absolute_ear.fileuri],
                       absolute_ear.target,
                       absolute_ear.dtype,
                       absolute_ear.shape,
                       loader=AstropyFITSLoader,
                       basepath=eitdir)


@pytest.fixture
def absolute_fl(absolute_ac):
    return absolute_ac._loader_array.flat[0]


def test_construct(relative_fl, absolute_fl):
    for fl in [relative_fl, absolute_fl]:
        assert fl.shape == (128, 128)
        assert fl.dtype == "float64"
        assert fl.absolute_uri == eitdir /"efz20040301.000010_s.fits"

        for contain in ("efz20040301.000010_s.fits", str(fl.shape), fl.dtype):
            assert contain in repr(fl)
            assert contain in str(fl)


def test_array(absolute_fl):
    a = absolute_fl.fits_array
    assert isinstance(a, np.ndarray)

    for contain in ("efz20040301.000010_s.fits", str(absolute_fl.shape), absolute_fl.dtype):
        assert contain in repr(absolute_fl)
        assert contain in str(absolute_fl)


def test_nan(relative_ac, tmpdir):
    relative_ac.basepath = tmpdir
    array = relative_ac._generate_array()
    assert_allclose(array[10:20, :], np.nan)


def test_np_array(absolute_fl):
    narr = np.array(absolute_fl)
    assert_allclose(narr, absolute_fl.fits_array)
    assert narr is not absolute_fl.fits_array

def test_slicing(absolute_fl):
    aslice = np.s_[10:20, 10:20]
    sarr = absolute_fl[aslice]

    assert_allclose(sarr, absolute_fl.fits_array[aslice])
