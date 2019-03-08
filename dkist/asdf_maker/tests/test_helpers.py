import os
from pathlib import Path

import numpy as np
import pytest

import asdf
import astropy.units as u
from astropy.io import fits
from astropy.modeling import Model
from astropy.modeling.models import Linear1D
from astropy.time import Time
from gwcs.lookup_table import LookupTable

from dkist.asdf_maker.generator import asdf_tree_from_filenames, headers_from_filenames
from dkist.asdf_maker.helpers import (linear_spectral_model, linear_time_model, make_asdf,
                                      references_from_filenames, spatial_model_from_header,
                                      spectral_model_from_framewave, time_model_from_date_obs)


def test_references_from_filesnames_shape_error(header_filenames):
    headers = headers_from_filenames(header_filenames, hdu=0)
    with pytest.raises(ValueError) as exc:
        references_from_filenames(header_filenames, headers, [2, 3])

        assert "incorrect number" in str(exc)
        assert "2, 3" in str(exc)
        assert str(len(header_filenames)) in str(exc)


def test_references_from_filenames(header_filenames):
    headers = headers_from_filenames(header_filenames, hdu=0)
    base = os.path.split(header_filenames[0])[0]
    refs = references_from_filenames(header_filenames, np.array(headers, dtype=object),
                                     (len(header_filenames),), relative_to=base)

    for ref in refs:
        assert base not in ref.fileuri


def first_header(header_filenames):
    return fits.getheader(header_filenames[0])


def test_spatial_model(header_filenames):
    spatial = spatial_model_from_header(first_header(header_filenames))
    assert isinstance(spatial, Model)


def test_spatial_model_fail(header_filenames):
    header = first_header(header_filenames)
    header['CTYPE2'] = 'WAVE'
    with pytest.raises(ValueError):
        spatial_model_from_header(header)


def test_linear_spectral():
    lin = linear_spectral_model(10*u.nm, 0*u.nm)
    assert isinstance(lin, Linear1D)
    assert u.allclose(lin.slope, 10*u.nm/u.pix)
    assert u.allclose(lin.intercept, 0*u.nm)


def test_linear_time():
    lin = linear_time_model(10*u.s)
    assert isinstance(lin, Linear1D)
    assert u.allclose(lin.slope, 10*u.s/u.pix)
    assert u.allclose(lin.intercept, 0*u.s)


def test_time_from_dateobs(header_filenames):
    date_obs = [fits.getheader(f)['DATE-OBS'] for f in header_filenames]
    time = time_model_from_date_obs(date_obs)
    assert isinstance(time, Linear1D)


def test_time_from_dateobs_lookup(header_filenames):
    date_obs = [fits.getheader(f)['DATE-OBS'] for f in header_filenames]
    date_obs[5] = (Time(date_obs[5]) + 10*u.s).isot
    time = time_model_from_date_obs(date_obs)
    assert isinstance(time, LookupTable)


def test_spectral_framewave(header_filenames):
    head = first_header(header_filenames)

    # Skip the VISP headers
    if "FRAMEWAV" not in head:
        return

    nwave = head['DNAXIS3']
    framewave = [fits.getheader(h)['FRAMEWAV'] for h in header_filenames]

    m = spectral_model_from_framewave(framewave[:nwave])
    assert isinstance(m, Linear1D)

    m2 = spectral_model_from_framewave(framewave)
    assert isinstance(m2, LookupTable)


def test_make_asdf(header_filenames, tmpdir):
    tree = asdf_tree_from_filenames(header_filenames, "test.asdf")
    fname = Path(tmpdir.join("test.asdf"))
    asdf_file = make_asdf(fname, dataset=tree['data'], gwcs=tree['wcs'])

    with open(asdf_file, "rb") as fd:
        af = asdf.AsdfFile()
        af = asdf.AsdfFile._open_asdf(af, fd)
