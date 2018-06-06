import os
import glob
from unittest.mock import patch

import pytest
from astropy.io import fits
from astropy.modeling import Model
import gwcs
import gwcs.coordinate_frames as cf

from dkist.data.test import rootdir
from dkist.asdf_maker.generator import TransformBuilder, gwcs_from_filenames


@pytest.fixture
def header_filenames():
    files = glob.glob(os.path.join(rootdir, 'datasetheaders', '*'))
    files.sort()
    return files


@pytest.fixture
def transform_builder():
    files = glob.glob(os.path.join(rootdir, 'datasetheaders', '*'))
    files.sort()
    headers = [fits.Header.fromtextfile(f) for f in files]
    return TransformBuilder(headers)


def test_reset(transform_builder):
    transform_builder._i = 2
    transform_builder.reset()
    assert transform_builder._i == 0


def test_transform(transform_builder):
    assert isinstance(transform_builder.transform, Model)


def test_frames(transform_builder):
    frames = transform_builder.frames
    assert all([isinstance(frame, cf.CoordinateFrame) for frame in frames])


def headers_from_textfiles(filenames, hdu=0):
    """
    This is a patched version of headers_from_filenames for testing with.
    """
    return (fits.Header.fromtextfile(fname) for fname in filenames)


@patch('dkist.asdf_maker.generator.headers_from_filenames', headers_from_textfiles)
def test_gwcs_from_files(header_filenames):
    w = gwcs_from_filenames(header_filenames)
    assert isinstance(w, gwcs.WCS)


