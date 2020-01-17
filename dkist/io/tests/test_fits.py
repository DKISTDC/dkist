from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_allclose

import asdf
from astropy.io import fits

from dkist.data.test import rootdir
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
def relative_fl(relative_ear):
    return AstropyFITSLoader(relative_ear, basepath=eitdir)


@pytest.fixture
def absolute_fl(absolute_ear):
    return AstropyFITSLoader(absolute_ear)


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
    assert absolute_fl._array is a
    assert absolute_fl._fits_header is not None
    assert absolute_fl.fits_header is absolute_fl._fits_header
    assert isinstance(absolute_fl.fits_header, fits.Header)

    for contain in ("efz20040301.000010_s.fits", str(absolute_fl.shape), absolute_fl.dtype):
        assert contain in repr(absolute_fl)
        assert contain in str(absolute_fl)


def test_nan():
    ear = asdf.ExternalArrayReference("/tmp/not_a_path.fits",
                                      0,
                                      "float64",
                                      (128, 128))
    loader = AstropyFITSLoader(ear)

    assert_allclose(loader[10:20, :], np.nan)


def test_header(absolute_fl):
    h = absolute_fl.fits_header
    assert isinstance(h, fits.Header)
    assert absolute_fl.fits_header is absolute_fl._fits_header


def test_np_array(absolute_fl):
    narr = np.array(absolute_fl)
    assert_allclose(narr, absolute_fl._array)
    assert narr is not absolute_fl._array


def test_slicing(absolute_fl):
    aslice = np.s_[10:20, 10:20]
    sarr = absolute_fl[aslice]

    assert_allclose(sarr, absolute_fl._array[aslice])
