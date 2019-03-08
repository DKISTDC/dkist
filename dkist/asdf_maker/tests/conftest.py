import os
import glob
import shutil
import tempfile
from zipfile import ZipFile

import pytest

from dkist.asdf_maker.generator import TransformBuilder, headers_from_filenames
from dkist.data.test import rootdir

DATA_DIR = os.path.join(rootdir, 'datasettestfiles')


def extract(name):
    atmpdir = tempfile.mkdtemp()
    with ZipFile(os.path.join(DATA_DIR, name)) as myzip:
        myzip.extractall(atmpdir)
    return atmpdir


@pytest.fixture(scope="session", params=["vtf.zip", "visp.zip"])
def header_filenames(request):
    tdir = extract(request.param)
    files = glob.glob(os.path.join(tdir, '*'))
    files.sort()
    yield files
    shutil.rmtree(tdir)


@pytest.fixture(params=["vtf.zip", "visp.zip"])
def transform_builder(request):
    tdir = extract(request.param)
    files = glob.glob(os.path.join(tdir, '*'))
    files.sort()
    headers = headers_from_filenames(files)
    yield TransformBuilder(headers)
    shutil.rmtree(tdir)


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
