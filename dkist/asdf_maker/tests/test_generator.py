import os
import glob

import pytest
from astropy.io import fits
from astropy.modeling import Model
import gwcs.coordinate_frames as cf

from dkist.data.test import rootdir
from dkist.asdf_maker.generator import TransformBuilder


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
