import os
import glob

import pytest
import numpy as np
from astropy.io import fits
from astropy.modeling import Model
import gwcs
import gwcs.coordinate_frames as cf

from dkist.asdf_maker.generator import TransformBuilder, gwcs_from_headers

from dkist.data.test import rootdir
HEADER_DIR = os.path.join(rootdir, 'datasetheaders')


def make_header_files():
    """
    This generates 20 test headers for the visp sp_5_raster

    It's here because I don't know where else to put it.
    """
    from dkistdataratemodel.units import frame
    from dkist_data_model.generator.dataproducts.visp import CalibratedVISP
    visp = CalibratedVISP(end_condition=20*frame)

    headers = np.array([header for header in visp.generate_metadata('sp_5_raster',
                                                                    metadata_type="file")])
    for i, (head, comments) in enumerate(headers):
        header = fits.Header(head)
        for k, c in comments.items():
            header.comments[k] = c
        header.totextfile(os.path.join(HEADER_DIR, f'visp_sp5_{i+1:02d}'), overwrite=True)


@pytest.fixture
def header_filenames():
    files = glob.glob(os.path.join(HEADER_DIR, '*'))
    files.sort()
    return files


@pytest.fixture
def transform_builder():
    files = glob.glob(os.path.join(HEADER_DIR, '*'))
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
    return [fits.Header.fromtextfile(fname) for fname in filenames]


def test_gwcs_from_files(header_filenames):
    w = gwcs_from_headers(headers_from_textfiles(header_filenames))
    assert isinstance(w, gwcs.WCS)
