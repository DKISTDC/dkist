import numpy as np
import pytest

import astropy.modeling.models as m
import astropy.units as u
from astropy.coordinates.matrix_utilities import rotation_matrix
from astropy.modeling import CompoundModel, Model
from astropy.modeling.separable import separability_matrix

from dkist.wcs.models import (CoupledCompoundModel, VaryingCelestialTransform,
                              VaryingCelestialTransform2D, VaryingCelestialTransformSlit,
                              VaryingCelestialTransformSlit2D)


@pytest.fixture
def linear_time():
    return m.Linear1D(slope=1*u.s/u.pix, intercept=0*u.s)


@pytest.fixture
def vct_crval():
    crval_table = ((0, 1), (2, 3), (4, 5)) * u.arcsec
    return VaryingCelestialTransform(crpix=(5, 5) * u.pix,
                                     cdelt=(1, 1) * u.arcsec/u.pix,
                                     crval_table=crval_table,
                                     pc_table=np.identity(2) * u.arcsec,
                                     lon_pole=180 * u.deg)


@pytest.fixture
def vct_2d_pc():
    varying_matrix_lt = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 15)] * u.arcsec
    varying_matrix_lt = varying_matrix_lt.reshape((5, 3, 2, 2))

    return VaryingCelestialTransform2D(crpix=(5, 5) * u.pix,
                                       cdelt=(1, 1) * u.arcsec/u.pix,
                                       crval_table=(0, 0) * u.arcsec,
                                       pc_table=varying_matrix_lt,
                                       lon_pole=180 * u.deg)


def test_coupled_init_error():
    with pytest.raises(ValueError, match="only be used with the & operator"):
        CoupledCompoundModel("|", None, None)


def test_coupled(vct_crval, linear_time):
    tfrm = CoupledCompoundModel("&", vct_crval, linear_time, shared_inputs=1)

    assert tfrm.n_inputs == 3
    assert len(tfrm.inputs) == 3

    pixel = (0, 0, 2) * u.pix
    world = tfrm(*pixel)
    spatial_world = vct_crval(*pixel)
    temporal_world = linear_time(pixel[2])
    assert u.allclose(spatial_world, world[:2])
    assert u.allclose(temporal_world, world[2])

    inverse = tfrm.inverse

    assert inverse.n_inputs == 3
    assert inverse.n_outputs == 3

    assert isinstance(inverse, CompoundModel)

    assert u.allclose(inverse(*world), pixel, atol=1e-9*u.pix)


def test_coupled_2d(vct_2d_pc, linear_time):
    double_time = linear_time & linear_time
    tfrm = CoupledCompoundModel("&", vct_2d_pc, double_time, shared_inputs=2)

    assert tfrm.n_inputs == 4
    assert len(tfrm.inputs) == 4

    pixel = (0, 0, 3, 2) * u.pix
    world = tfrm(*pixel)
    spatial_world = vct_2d_pc(*pixel)
    temporal_world = double_time(*pixel[-2:])
    assert u.allclose(spatial_world, world[:2])
    assert u.allclose(temporal_world, world[-2:])

    inverse = tfrm.inverse

    assert inverse.n_inputs == 4
    assert inverse.n_outputs == 4

    assert isinstance(inverse, CompoundModel)

    assert u.allclose(inverse(*world), pixel, atol=1e-9*u.pix)


def test_coupled_sep(linear_time, vct_crval):
    if not hasattr(Model, "_calculate_separability_matrix"):
        pytest.skip()

    tfrm = CoupledCompoundModel("&", vct_crval, linear_time, shared_inputs=1)
    smatrix = separability_matrix(tfrm)
    assert np.allclose(smatrix, np.array([[1, 1, 1],
                                          [1, 1, 1],
                                          [0, 0, 1]]))


def test_coupled_sep_2d(vct_2d_pc, linear_time):
    if not hasattr(Model, "_calculate_separability_matrix"):
        pytest.skip()
    linear_spectral = m.Linear1D(slope=10*u.nm/u.pix)
    right = linear_time & linear_spectral
    tfrm = CoupledCompoundModel("&", vct_2d_pc, right, shared_inputs=2)

    smatrix = separability_matrix(tfrm)
    assert np.allclose(smatrix, np.array([[1, 1, 1, 1],
                                          [1, 1, 1, 1],
                                          [0, 0, 1, 0],
                                          [0, 0, 0, 1]]))


def test_coupled_sep_2d_extra(vct_2d_pc, linear_time):
    if not hasattr(Model, "_calculate_separability_matrix"):
        pytest.skip()
    linear_spectral = m.Linear1D(slope=10*u.nm/u.pix)
    right = linear_time & linear_spectral & linear_spectral
    tfrm = CoupledCompoundModel("&", vct_2d_pc, right, shared_inputs=2)

    smatrix = separability_matrix(tfrm)
    assert np.allclose(smatrix, np.array([[1, 1, 1, 1, 0],
                                          [1, 1, 1, 1, 0],
                                          [0, 0, 1, 0, 0],
                                          [0, 0, 0, 1, 0],
                                          [0, 0, 0, 0, 1]]))


def test_coupled_slit_no_repeat(linear_time):
    pc_table = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 10)] * u.arcsec

    kwargs = dict(crpix=(5, 5) * u.pix,
                  cdelt=(1, 1) * u.arcsec/u.pix,
                  crval_table=(0, 0) * u.arcsec,
                  lon_pole=180 * u.deg)

    vct_slit = VaryingCelestialTransformSlit(pc_table=pc_table, **kwargs)

    tfrm = CoupledCompoundModel("&", vct_slit, linear_time, shared_inputs=1)
    pixel = (0*u.pix, 4*u.pix)
    world = tfrm(*pixel)
    ipixel = tfrm.inverse(*world)
    assert u.allclose(ipixel, pixel, atol=1e-5*u.pix)


def test_coupled_slit_with_repeat(linear_time):
    pc_table = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 15)] * u.arcsec
    pc_table = pc_table.reshape((5, 3, 2, 2))

    kwargs = dict(crpix=(5, 5) * u.pix,
                  cdelt=(1, 1) * u.arcsec/u.pix,
                  crval_table=(0, 0) * u.arcsec,
                  lon_pole=180 * u.deg)

    vct_slit = VaryingCelestialTransformSlit2D(pc_table=pc_table, **kwargs)

    tfrm = CoupledCompoundModel("&", vct_slit, linear_time & linear_time, shared_inputs=2)
    pixel = (0*u.pix, 0*u.pix, 0*u.pix)
    world = tfrm(*pixel)
    ipixel = tfrm.inverse(*world)
    assert u.allclose(ipixel, pixel, atol=1e-5*u.pix)
