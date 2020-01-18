import os
import glob
import tempfile
from zipfile import ZipFile

import pytest

from dkist.data.test import rootdir
from dkist.io.asdf.generator.generator import headers_from_filenames
from dkist.io.asdf.generator.transforms import TransformBuilder

DATA_DIR = os.path.join(rootdir, 'datasettestfiles')


@pytest.fixture(scope="session", params=["vtf.zip", "visp.zip"])
def header_directory(request):
    atmpdir = tempfile.mkdtemp()
    with ZipFile(os.path.join(DATA_DIR, request.param)) as myzip:
        myzip.extractall(atmpdir)
    return atmpdir


@pytest.fixture
def header_filenames(header_directory):
    files = glob.glob(os.path.join(header_directory, '*'))
    files.sort()
    return files


@pytest.fixture
def transform_builder(header_filenames):
    headers = headers_from_filenames(header_filenames)
    return TransformBuilder(headers)


def make_header_files():
    """
    This generates 20 test headers for the visp sp_5_raster

    It's here because I don't know where else to put it.
    """
    os.makedirs(DATA_DIR) if not os.path.exists(DATA_DIR) else None
    from dkistdataratemodel.units import frame
    from dkist_data_model.generator.dataproducts.visp import CalibratedVISP

    """
    Generate VISP
    """
    visp = CalibratedVISP(end_condition=20*frame)

    visp_files = visp.to_fits("sp_5_labelled",
                              path_template=os.path.join(DATA_DIR, 'visp_5d_{i:02d}.fits'))

    with ZipFile(os.path.join(DATA_DIR, "visp.zip"), "w") as myzip:
        for fname in visp_files:
            myzip.write(fname, os.path.split(fname)[1])
            os.remove(fname)

    """
    Generate VTF
    """
    from dkist_data_model.generator.dataproducts.vtf import CalibratedVTF
    vtf = CalibratedVTF(end_condition=96*frame)

    vtf_files = vtf.to_fits("5d_test",
                            path_template=os.path.join(DATA_DIR, 'vtf_5d_{i:02d}.fits'))

    with ZipFile(os.path.join(DATA_DIR, "vtf.zip"), "w") as myzip:
        for fname in vtf_files:
            myzip.write(fname, os.path.split(fname)[1])
            os.remove(fname)


# If we just run this file, then make the header zips
if __name__ == '__main__':
    make_header_files()
