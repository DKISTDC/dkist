import os
import tempfile
import glob
from zipfile import ZipFile
from unittest.mock import patch

import asdf
import pytest
import numpy as np
from astropy.io import fits
from astropy.modeling import Model
import gwcs
import gwcs.coordinate_frames as cf

from dkist.asdf_maker.helpers import make_asdf
from dkist.asdf_maker.generator import (TransformBuilder, gwcs_from_headers,
                                        asdf_tree_from_filenames,
                                        headers_from_filenames, validate_headers)

from dkist.data.test import rootdir

DATA_DIR = os.path.join(rootdir, 'datasettestfiles')


def make_header_files():
    """
    This generates 20 test headers for the visp sp_5_raster

    It's here because I don't know where else to put it.
    """
    os.makedirs(DATA_DIR) if not os.path.exists(DATA_DIR) else None
    from dkistdataratemodel.units import frame
    from dkist_data_model.generator.dataproducts.visp import CalibratedVISP
    visp = CalibratedVISP(end_condition=20*frame)

    visp_files = visp.to_fits("sp_5_labelled",
                              path_template=os.path.join(DATA_DIR, 'visp_5d_{i:02d}.fits'))

    with ZipFile(os.path.join(DATA_DIR, "visp.zip"), "w") as myzip:
        for fname in visp_files:
            myzip.write(fname, os.path.split(fname)[1])
            os.remove(fname)

    from dkist_data_model.generator.dataproducts.vtf import CalibratedVTF
    vtf = CalibratedVTF(end_condition=96*frame)

    vtf_files = vtf.to_fits("5d_test",
                            path_template=os.path.join(DATA_DIR, 'vtf_5d_{i:02d}.fits'))

    with ZipFile(os.path.join(DATA_DIR, "vtf.zip"), "w") as myzip:
        for fname in vtf_files:
            myzip.write(fname, os.path.split(fname)[1])
            os.remove(fname)


def extract(name):
    atmpdir = tempfile.mkdtemp()
    with ZipFile(os.path.join(DATA_DIR, name)) as myzip:
        myzip.extractall(atmpdir)
    return atmpdir


@pytest.fixture(params=["vtf.zip", "visp.zip"])
def header_filenames(request):
    files = glob.glob(os.path.join(extract(request.param), '*'))
    files.sort()
    return files


@pytest.fixture(params=["vtf.zip", "visp.zip"])
def transform_builder(request):
    files = glob.glob(os.path.join(extract(request.param), '*'))
    files.sort()
    headers = headers_from_filenames(files)
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


def test_gwcs_from_files(header_filenames):
    w = gwcs_from_headers(headers_from_filenames(header_filenames))
    assert isinstance(w, gwcs.WCS)


def test_asdf_tree(header_filenames):
    tree = asdf_tree_from_filenames(header_filenames)
    assert isinstance(tree, dict)


def test_validator(header_filenames):
    headers = headers_from_filenames(header_filenames)
    headers[10]['NAXIS'] = 5
    with pytest.raises(ValueError) as excinfo:
        validate_headers(headers)
        assert "NAXIS" in str(excinfo)
