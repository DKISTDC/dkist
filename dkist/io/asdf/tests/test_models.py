import numpy as np
import pytest

import astropy.modeling.models as m
import astropy.units as u
from asdf.testing.helpers import roundtrip_object
from astropy.coordinates.matrix_utilities import rotation_matrix
from astropy.modeling import CompoundModel

from dkist.wcs.models import (
    CoupledCompoundModel,
    InverseVaryingCelestialTransform,
    InverseVaryingCelestialTransform2D,
    Ravel,
    RefractedAngleSineModel,
    Unravel,
    VaryingCelestialTransform,
    VaryingCelestialTransform2D,
    WavelengthFromGrismEquation,
    build_grating_spectral_transform,
    varying_celestial_transform_from_tables,
)


def test_roundtrip_vct():
    varying_matrix_lt = [rotation_matrix(a)[:2, :2]
                         for a in np.linspace(0, 90, 10)] * u.pix

    vct = VaryingCelestialTransform(crpix_table=(5, 5) * u.pix,
                                    cdelt=(1, 1) * u.arcsec/u.pix,
                                    crval_table=(0, 0) * u.arcsec,
                                    pc_table=varying_matrix_lt,
                                    lon_pole=180 * u.deg)
    new_vct = roundtrip_object(vct)
    assert isinstance(new_vct, VaryingCelestialTransform)
    new_ivct = roundtrip_object(vct.inverse)
    assert isinstance(new_ivct, InverseVaryingCelestialTransform)

    assert u.allclose(u.Quantity(new_vct.crpix_table), (5, 5) * u.pix)
    assert u.allclose(u.Quantity(new_ivct.crpix_table), (5, 5) * u.pix)

    assert u.allclose(u.Quantity(new_vct.pc_table), varying_matrix_lt)
    assert u.allclose(u.Quantity(new_ivct.pc_table), varying_matrix_lt)

    pixel = (0*u.pix, 0*u.pix, 5*u.pix)
    world = new_vct(*pixel)
    assert u.allclose(world, (359.99804329*u.deg, 0.00017119*u.deg))

    assert u.allclose(new_ivct(*world, 5*u.pix), pixel[:2], atol=0.01*u.pix)


def test_roundtrip_vct_2d():
    varying_matrix_lt = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 15)] * u.pix
    varying_matrix_lt = varying_matrix_lt.reshape((5, 3, 2, 2))

    vct = VaryingCelestialTransform2D(crpix_table=(5, 5) * u.pix,
                                      cdelt=(1, 1) * u.arcsec/u.pix,
                                      crval_table=(0, 0) * u.arcsec,
                                      pc_table=varying_matrix_lt,
                                      lon_pole=180 * u.deg)
    new_vct = roundtrip_object(vct)
    assert isinstance(new_vct, VaryingCelestialTransform2D)
    new_ivct = roundtrip_object(vct.inverse)
    assert isinstance(new_ivct, InverseVaryingCelestialTransform2D)

    assert u.allclose(u.Quantity(new_vct.crpix_table), (5, 5) * u.pix)
    assert u.allclose(u.Quantity(new_ivct.crpix_table), (5, 5) * u.pix)

    assert u.allclose(u.Quantity(new_vct.pc_table), varying_matrix_lt)
    assert u.allclose(u.Quantity(new_ivct.pc_table), varying_matrix_lt)

    pixel = (0*u.pix, 0*u.pix, 4*u.pix, 2*u.pix)
    world = new_vct(*pixel)
    assert u.allclose(world, (359.99861111, 0.00138889)*u.deg)

    assert u.allclose(new_ivct(*world, 4*u.pix, 2*u.pix), pixel[:2], atol=0.01*u.pix)


def test_roundtrip_vct_slit():
    varying_matrix_lt = [rotation_matrix(a)[:2, :2]
                         for a in np.linspace(0, 90, 10)] * u.pix

    vct = varying_celestial_transform_from_tables(crpix_table=(5, 5) * u.pix,
                                                  cdelt=(1, 1) * u.arcsec/u.pix,
                                                  crval_table=(0, 0) * u.arcsec,
                                                  pc_table=varying_matrix_lt,
                                                  lon_pole=180 * u.deg,
                                                  slit=0)
    new_vct = roundtrip_object(vct)
    assert isinstance(new_vct, CompoundModel)
    new_ivct = roundtrip_object(vct.inverse)
    assert isinstance(new_ivct, CompoundModel)


def test_roundtrip_vct_slit2d():
    varying_matrix_lt = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 15)] * u.pix
    varying_matrix_lt = varying_matrix_lt.reshape((5, 3, 2, 2))

    vct = varying_celestial_transform_from_tables(crpix_table=(5, 5) * u.pix,
                                                  cdelt=(1, 1) * u.arcsec/u.pix,
                                                  crval_table=(0, 0) * u.arcsec,
                                                  pc_table=varying_matrix_lt,
                                                  lon_pole=180 * u.deg,
                                                  slit=0)
    new_vct = roundtrip_object(vct)
    assert isinstance(new_vct, CompoundModel)
    new_ivct = roundtrip_object(vct.inverse)
    assert isinstance(new_ivct, CompoundModel)


def test_coupled_compound_model():
    ccm = CoupledCompoundModel("&", m.Shift(5), m.Scale(10))
    new = roundtrip_object(ccm)
    assert isinstance(new, CoupledCompoundModel)
    assert isinstance(new.left, m.Shift)
    assert isinstance(new.right, m.Scale)

    assert ccm.n_inputs == new.n_inputs
    assert ccm.inputs == new.inputs


def test_coupled_compound_model_nested():
    ccm = CoupledCompoundModel("&", m.Shift(5) & m.Scale(2), m.Scale(10) | m.Shift(3))
    new = roundtrip_object(ccm)
    assert isinstance(new, CoupledCompoundModel)
    assert isinstance(new.left, CompoundModel)
    assert isinstance(new.left.left, m.Shift)
    assert isinstance(new.left.right, m.Scale)
    assert isinstance(new.right, CompoundModel)
    assert isinstance(new.right.left, m.Scale)
    assert isinstance(new.right.right, m.Shift)

    assert ccm.n_inputs == new.n_inputs
    assert ccm.inputs == new.inputs


def test_ravel_model():
    ravel = Ravel((10, 10))
    new = roundtrip_object(ravel)

    assert isinstance(new, Ravel)
    assert isinstance(new.inverse, Unravel)

    assert new.array_shape == ravel.array_shape


GRISM_PARAMS = {
    "reference_pixel": 217.0,
    "reference_wavelength": 854.1738582455826 * u.nm,
    "dispersion": 0.0022975580183395555 * u.nm / u.pix,
    "groove_density": 23000.0 / u.m,
    "spectral_order": 90 * u.one,
    "incident_angle": 65.696 * u.deg,
    "refractive_index": 1.25 * u.one,
    "refractive_index_derivative": 1000.0 / u.m,
    "out_of_plane_angle": 1.5 * u.deg,
    "camera_angle": 0.8 * u.deg,
}


@pytest.mark.parametrize("with_grism_terms", [True, False])
def test_roundtrip_refracted_angle_sine_model(with_grism_terms):
    params = dict(GRISM_PARAMS)
    if not with_grism_terms:
        # Identity-valued Quantities, as build_grating_spectral_transform passes
        # when a header has no grism correction terms.
        params.update(refractive_index=1 * u.one, refractive_index_derivative=0 / u.m,
                      out_of_plane_angle=0 * u.deg, camera_angle=0 * u.deg)
    model = RefractedAngleSineModel(**params)
    new_model = roundtrip_object(model)

    assert isinstance(new_model, RefractedAngleSineModel)
    for name in model.param_names:
        old_param, new_param = getattr(model, name), getattr(new_model, name)
        assert new_param.unit == old_param.unit
        assert np.allclose(new_param.value, old_param.value)
    pixels = np.array([0.0, 100.0, 217.0, 511.0])
    assert u.allclose(new_model(pixels), model(pixels))


def test_roundtrip_refracted_angle_sine_model_bare_numbers():
    model = RefractedAngleSineModel(
        reference_pixel=10,
        reference_wavelength=5e-7,
        dispersion=1e-12,
        groove_density=2e6,
        spectral_order=1,
        incident_angle=np.pi / 6,
    )
    new_model = roundtrip_object(model)
    pixels = np.array([0.0, 10.0, 20.0])
    np.testing.assert_allclose(new_model(pixels), model(pixels))


@pytest.mark.parametrize("with_grism_terms", [True, False])
def test_roundtrip_wavelength_from_grism_equation(with_grism_terms):
    kwargs = {"groove_density": GRISM_PARAMS["groove_density"], "spectral_order": GRISM_PARAMS["spectral_order"]}
    if with_grism_terms:
        kwargs.update({name: GRISM_PARAMS[name] for name in
                       ("reference_wavelength", "refractive_index", "refractive_index_derivative", "out_of_plane_angle")})
    else:
        kwargs.update(reference_wavelength=GRISM_PARAMS["reference_wavelength"], refractive_index=1 * u.one,
                      refractive_index_derivative=0 / u.m, out_of_plane_angle=0 * u.deg)
    model = WavelengthFromGrismEquation(**kwargs)
    new_model = roundtrip_object(model)

    assert isinstance(new_model, WavelengthFromGrismEquation)
    alpha_in = np.sin(GRISM_PARAMS["incident_angle"])
    alpha_out = np.array([0.24, 0.25, 0.26]) * u.one
    assert u.allclose(new_model(alpha_in, alpha_out), model(alpha_in, alpha_out))


@pytest.mark.parametrize("with_grism_terms", [True, False])
def test_roundtrip_grating_spectral_transform(with_grism_terms):
    params = dict(GRISM_PARAMS)
    if not with_grism_terms:
        # Fall back to the builder's identity defaults.
        for name in ("refractive_index", "refractive_index_derivative", "out_of_plane_angle", "camera_angle"):
            params.pop(name)
    transform = build_grating_spectral_transform(**params)
    new_transform = roundtrip_object(transform)

    assert isinstance(new_transform, CompoundModel)
    pixels = np.array([0.0, 100.0, 217.0, 300.0, 511.0])
    assert u.allclose(new_transform(pixels), transform(pixels))
