"""
Tests for the FITS -GRA/-GRI grism models.

Ported from the original implementation proposed upstream in gwcs#745.
"""
import numpy as np
import pytest
from numpy.testing import assert_allclose

import astropy.units as u
from astropy.wcs import WCS

from dkist.wcs.models import (
    PixelFromGrismWavelength,
    RefractedAngleSineModel,
    WavelengthFromGrismEquation,
    build_grating_spectral_transform,
)


def test_wavelength_grism_equation_incompatible_units_raises() -> None:
    """Passing units that are incompatible with 1/length for groove_density should
    raise UnitConversionError rather than silently producing a wrong result."""
    model = WavelengthFromGrismEquation(
        groove_density=20000 / u.m,
        spectral_order=-1,
        reference_wavelength=854.1738582455826 * u.nm,
        refractive_index_derivative=1000 * u.m,  # wrong: should be 1/length
    )
    alpha_in = np.sin(65.0 * u.deg)
    with pytest.raises(u.UnitConversionError):
        model(alpha_in, alpha_in)


def test_refracted_angle_sine_model_basic() -> None:
    """Output should be the sine of the refracted angle at the reference pixel."""
    groove_density = 23000 / u.m
    spectral_order = 90 * u.one
    incident_angle = 65.696 * u.deg
    refractive_index = 1.25 * u.one
    refractive_index_derivative = 1000 / u.m
    out_of_plane_angle = 1.5 * u.deg
    model = RefractedAngleSineModel(
        reference_pixel=217,
        reference_wavelength=854.1738582455826 * u.nm,
        dispersion=0.0022975580183395555 * u.nm / u.pix,
        groove_density=groove_density,
        spectral_order=spectral_order,
        incident_angle=incident_angle,
        refractive_index=refractive_index,
        refractive_index_derivative=refractive_index_derivative,
        out_of_plane_angle=out_of_plane_angle,
        camera_angle=0 * u.deg,
    )

    grism_constant = (groove_density * spectral_order) / np.cos(out_of_plane_angle)
    reference_refracted_angle = np.arcsin(
        (grism_constant * (854.1738582455826 * u.nm))
        - refractive_index * np.sin(incident_angle)
    )
    result = model(217)
    assert u.allclose(result, np.sin(reference_refracted_angle), atol=1e-12)


def test_refracted_angle_sine_model_bare_numbers() -> None:
    """Plain-number parameters work, with angles in radians.

    With ``groove_density * spectral_order * reference_wavelength = 1`` and
    ``sin(incident_angle) = 0.5``, the reference refracted angle is
    ``arcsin(0.5) = pi/6``. The dispersion is chosen so that one pixel away the
    arctan term is ``pi/12``, giving ``sin(pi/6 + pi/12) = sin(pi/4)``.
    """
    groove_density = 2e6
    dispersion = np.tan(np.pi / 12) * np.cos(np.pi / 6) / groove_density
    model = RefractedAngleSineModel(
        reference_pixel=10,
        reference_wavelength=5e-7,
        dispersion=dispersion,
        groove_density=groove_density,
        spectral_order=1,
        incident_angle=np.pi / 6,
    )
    result = model(np.array([10.0, 11.0]))
    assert not isinstance(result, u.Quantity)
    assert_allclose(result, [0.5, np.sqrt(2) / 2])


def test_wavelength_grism_equation_bare_numbers() -> None:
    """Plain-number parameters reduce to the classic grating equation by default."""
    model = WavelengthFromGrismEquation(groove_density=1e6, spectral_order=1)
    result = model(0.2, 0.3)
    assert not isinstance(result, u.Quantity)
    assert_allclose(result, 5e-7)


def test_refracted_angle_sine_model_defaults_return_zero() -> None:
    """The default model should produce a zero refracted-angle sine."""
    model = RefractedAngleSineModel()

    pixels = np.array([0.0, 1.0, 10.0, 100.0])
    result = model(pixels)

    assert u.allclose(result, np.zeros_like(pixels))


def test_refracted_angle_sine_model_invalid_arcsin_domain_raises() -> None:
    """Invalid parameter combinations should raise rather than return nan."""
    model = RefractedAngleSineModel(
        reference_wavelength=2000 * u.nm,
        groove_density=60000 / u.m,
        spectral_order=90 * u.one,
        incident_angle=10 * u.deg,
        refractive_index=1.0 * u.one,
    )

    with pytest.raises(ValueError, match="outside the valid arcsin domain"):
        model(0)


def test_refracted_angle_sine_model_matches_manual() -> None:
    """Result should match a manually computed refracted-angle sine."""
    reference_pixel = 217.0
    reference_wavelength = 854.1738582455826 * u.nm
    dispersion = 0.0022975580183395555 * u.nm / u.pix
    groove_density = 23000.0 / u.m
    spectral_order = 90 * u.one
    incident_angle = 65.696 * u.deg
    refractive_index = 1.25 * u.one
    refractive_index_derivative = 1000.0 / u.m
    out_of_plane_angle = 1.5 * u.deg
    camera_angle = 0.8 * u.deg

    model = RefractedAngleSineModel(
        reference_pixel=reference_pixel,
        reference_wavelength=reference_wavelength,
        dispersion=dispersion,
        groove_density=groove_density,
        spectral_order=spectral_order,
        incident_angle=incident_angle,
        refractive_index=refractive_index,
        refractive_index_derivative=refractive_index_derivative,
        out_of_plane_angle=out_of_plane_angle,
        camera_angle=camera_angle,
    )

    grism_constant = (groove_density * spectral_order) / np.cos(out_of_plane_angle)
    reference_refracted_angle = np.arcsin(
        (grism_constant * reference_wavelength)
        - refractive_index * np.sin(incident_angle)
    )
    grism_parameter_per_wavelength = (
        grism_constant - refractive_index_derivative * np.sin(incident_angle)
    ) / (np.cos(reference_refracted_angle) * np.cos(camera_angle) ** 2)

    pixels = np.array([0.0, 100.0, 217.0, 300.0, 511.0])
    wavelength_offset = ((pixels - reference_pixel) * u.pix) * dispersion
    expected_angle = (
        np.arctan(
            -np.tan(camera_angle) + wavelength_offset * grism_parameter_per_wavelength
        )
        + reference_refracted_angle
        + camera_angle
    )
    expected = np.sin(expected_angle)
    result = model(pixels)
    assert u.allclose(result, expected, atol=1e-12)


def test_wavelength_grism_equation_defaults():
    model = WavelengthFromGrismEquation(
        groove_density=20000 / u.m, spectral_order=-1
    )
    assert model.reference_wavelength.value == 0
    assert model.refractive_index.value == 1
    assert model.refractive_index_derivative.value == 0
    assert model.out_of_plane_angle.value == 0


def test_wavelength_grism_equation_reference_pixel():
    params = {
        "reference_pixel": 217.0,
        "reference_wavelength": 854.1738582455826 * u.nm,
        "dispersion": 0.0022975580183395555 * u.nm / u.pix,
        "grating_density": 23000.0 / u.m,
        "spectral_order": 90,
        "incident_angle": 65.696 * u.deg,
        "refractive_index": 1.25,
        "refractive_index_derivative": 1000.0 / u.m,
        "out_of_plane_angle": 1.5 * u.deg,
        "camera_angle": 0.8 * u.deg,
    }
    model = WavelengthFromGrismEquation(
        groove_density=params["grating_density"],
        spectral_order=params["spectral_order"],
        reference_wavelength=params["reference_wavelength"],
        refractive_index=params["refractive_index"],
        refractive_index_derivative=params["refractive_index_derivative"],
        out_of_plane_angle=params["out_of_plane_angle"],
    )

    grism_constant = (params["grating_density"] * params["spectral_order"]) / np.cos(
        params["out_of_plane_angle"]
    )
    reference_refracted_angle = np.arcsin(
        (grism_constant * params["reference_wavelength"])
        - params["refractive_index"] * np.sin(params["incident_angle"])
    )
    incident_angle_sine = np.sin(params["incident_angle"])
    dispersion_denominator = (
        (params["grating_density"] * params["spectral_order"])
        / np.cos(params["out_of_plane_angle"])
        - params["refractive_index_derivative"] * incident_angle_sine
    ) / params["spectral_order"]

    alpha_in = incident_angle_sine
    alpha_out = np.sin(reference_refracted_angle)
    result = model(alpha_in, alpha_out)
    expected = (
        (
            params["refractive_index"]
            - params["refractive_index_derivative"] * params["reference_wavelength"]
        )
        * incident_angle_sine
        + np.sin(reference_refracted_angle)
    ) / (dispersion_denominator * params["spectral_order"])

    assert u.allclose(result, expected)


def test_grism_models_recover_reference_wavelength_at_reference_pixel() -> None:
    """The reference pixel should map back to the reference wavelength."""
    reference_pixel = 217.0
    reference_wavelength = 854.1738582455826 * u.nm
    groove_density = 23000.0 / u.m
    spectral_order = 90
    incident_angle = 65.696 * u.deg
    refractive_index = 1.25 * u.one
    refractive_index_derivative = 1000.0 / u.m
    out_of_plane_angle = 1.5 * u.deg
    camera_angle = 0.8 * u.deg

    alpha_out_model = RefractedAngleSineModel(
        reference_pixel=reference_pixel,
        reference_wavelength=reference_wavelength,
        dispersion=0.0022975580183395555 * u.nm / u.pix,
        groove_density=groove_density,
        spectral_order=spectral_order,
        incident_angle=incident_angle,
        refractive_index=refractive_index,
        refractive_index_derivative=refractive_index_derivative,
        out_of_plane_angle=out_of_plane_angle,
        camera_angle=camera_angle,
    )
    wavelength_model = WavelengthFromGrismEquation(
        groove_density=groove_density,
        spectral_order=spectral_order,
        reference_wavelength=reference_wavelength,
        refractive_index=refractive_index,
        refractive_index_derivative=refractive_index_derivative,
        out_of_plane_angle=out_of_plane_angle,
    )

    alpha_in = np.sin(incident_angle)
    alpha_out = alpha_out_model(reference_pixel)
    result = wavelength_model(alpha_in, alpha_out)

    assert u.allclose(result, reference_wavelength)


def test_wavelength_grism_equation_matches_closed_form_for_pixel_array():
    params = {
        "reference_pixel": 217.0,
        "reference_wavelength": 854.1738582455826 * u.nm,
        "dispersion": 0.0022975580183395555 * u.nm / u.pix,
        "grating_density": 23000.0 / u.m,
        "spectral_order": 90,
        "incident_angle": 65.696 * u.deg,
        "refractive_index": 1.25,
        "refractive_index_derivative": 1000.0 / u.m,
        "out_of_plane_angle": 1.5 * u.deg,
        "camera_angle": 0.8 * u.deg,
    }
    model = WavelengthFromGrismEquation(
        groove_density=params["grating_density"],
        spectral_order=params["spectral_order"],
        reference_wavelength=params["reference_wavelength"],
        refractive_index=params["refractive_index"],
        refractive_index_derivative=params["refractive_index_derivative"],
        out_of_plane_angle=params["out_of_plane_angle"],
    )

    grism_constant = (params["grating_density"] * params["spectral_order"]) / np.cos(
        params["out_of_plane_angle"]
    )
    reference_refracted_angle = np.arcsin(
        (grism_constant * params["reference_wavelength"])
        - params["refractive_index"] * np.sin(params["incident_angle"])
    )
    grism_parameter_per_wavelength = (
        grism_constant
        - params["refractive_index_derivative"] * np.sin(params["incident_angle"])
    ) / (np.cos(reference_refracted_angle) * np.cos(params["camera_angle"]) ** 2)
    pixels = np.array([0.0, 100.0, 217.0, 300.0, 511.0])
    wavelength_offset = ((pixels - params["reference_pixel"]) * u.pix) * params[
        "dispersion"
    ]
    refracted_angle_sine = np.sin(
        np.arctan(
            -np.tan(params["camera_angle"])
            + wavelength_offset * grism_parameter_per_wavelength
        )
        + reference_refracted_angle
        + params["camera_angle"]
    )
    incident_angle_sine = np.sin(params["incident_angle"])
    dispersion_denominator = (
        (params["grating_density"] * params["spectral_order"])
        / np.cos(params["out_of_plane_angle"])
        - params["refractive_index_derivative"] * incident_angle_sine
    ) / params["spectral_order"]
    expected = (
        (
            params["refractive_index"]
            - params["refractive_index_derivative"] * params["reference_wavelength"]
        )
        * incident_angle_sine
        + refracted_angle_sine
    ) / (dispersion_denominator * params["spectral_order"])

    alpha_in = incident_angle_sine
    alpha_out = refracted_angle_sine
    result = model(alpha_in, alpha_out)

    assert_allclose(result, expected, rtol=1e-12, atol=1e-12)


def test_wavelength_grism_equation_near_zero_dispersion_denominator_raises() -> None:
    model = WavelengthFromGrismEquation(
        groove_density=1 / u.m,
        spectral_order=1,
        reference_wavelength=0 * u.m,
        refractive_index=1 * u.one,
        refractive_index_derivative=1 / u.m,
        out_of_plane_angle=0 * u.deg,
    )

    with pytest.raises(ValueError, match="dispersion denominator is too close to zero"):
        model(1 * u.one, 0 * u.one)


def test_wavelength_grism_equation_matches_astropy():
    header = {
        "CTYPE1": "AWAV-GRA",
        "CUNIT1": "nm",
        "CRPIX1": 218,
        "CRVAL1": 854.1738582455826,
        "CDELT1": 0.0022975580183395555,
        "PV1_0": 23000.0,
        "PV1_1": 90,
        "PV1_2": 65.696,
        "PV1_3": 1.25,
        "PV1_4": 1000.0,
        "PV1_5": 1.5,
        "PV1_6": 0.8,
    }
    model = WavelengthFromGrismEquation(
        groove_density=header["PV1_0"] / u.m,
        spectral_order=header["PV1_1"],
        reference_wavelength=header["CRVAL1"] * u.nm,
        refractive_index=header["PV1_3"] * u.one,
        refractive_index_derivative=header["PV1_4"] / u.m,
        out_of_plane_angle=header["PV1_5"] * u.deg,
    )

    pixels = np.array([0, 100, 217, 300, 511], dtype=float)
    reference_pixel = header["CRPIX1"] - 1
    reference_wavelength = header["CRVAL1"] * u.nm
    dispersion = header["CDELT1"] * u.nm / u.pix
    refractive_index = header["PV1_3"]
    camera_angle = header["PV1_6"] * u.deg

    incident_angle_sine = np.sin(header["PV1_2"] * u.deg)
    grism_constant = ((header["PV1_0"] / u.m) * (header["PV1_1"])) / np.cos(
        header["PV1_5"] * u.deg
    )
    reference_refracted_angle = np.arcsin(
        (grism_constant * reference_wavelength) - refractive_index * incident_angle_sine
    )
    grism_parameter_per_wavelength = (
        grism_constant - (header["PV1_4"] / u.m) * incident_angle_sine
    ) / (np.cos(reference_refracted_angle) * np.cos(camera_angle) ** 2)
    wavelength_offset = ((pixels - reference_pixel) * u.pix) * dispersion
    alpha_out = np.sin(
        np.arctan(
            -np.tan(camera_angle) + wavelength_offset * grism_parameter_per_wavelength
        )
        + reference_refracted_angle
        + camera_angle
    )
    alpha_in = incident_angle_sine

    expected = WCS(header).spectral.pixel_to_world(pixels)
    result = model(alpha_in, alpha_out)

    assert_allclose(
        result.to_value(u.nm), expected.to_value(u.nm), rtol=1e-10, atol=1e-10
    )


# The same grating and detector geometry given as plain numbers (lengths in m,
# angles in radians) and as Quantities.
PLAIN_PARAMETERS = {
    "reference_wavelength": 854.1738582455826e-9,
    "dispersion": 0.0022975580183395555e-9,
    "groove_density": 23000.0,
    "spectral_order": 90,
    "incident_angle": np.deg2rad(65.696),
}
QUANTITY_PARAMETERS = {
    "reference_wavelength": 854.1738582455826 * u.nm,
    "dispersion": 0.0022975580183395555 * u.nm / u.pix,
    "groove_density": 23000.0 / u.m,
    "spectral_order": 90,
    "incident_angle": 65.696 * u.deg,
    "refractive_index_derivative": 0 / u.m,
}


@pytest.mark.parametrize("pixel_unit", [pytest.param(1, id="pixel_plain"), pytest.param(u.pix, id="pixel_pix")])
@pytest.mark.parametrize(
    "reference_pixel_unit", [pytest.param(1, id="reference_pixel_plain"), pytest.param(u.pix, id="reference_pixel_pix")]
)
@pytest.mark.parametrize(
    "parameters",
    [pytest.param(PLAIN_PARAMETERS, id="parameters_plain"), pytest.param(QUANTITY_PARAMETERS, id="parameters_quantity")],
)
def test_refracted_angle_sine_model_unit_combinations(pixel_unit, reference_pixel_unit, parameters):
    """
    Given: a RefractedAngleSineModel whose reference pixel, and the pixels it is evaluated at,
           are each plain numbers or in u.pix, with plain-number or Quantity parameters
    When: the model is evaluated
    Then: every combination gives the same result as plain numbers throughout
    """
    pixels = np.array([0.0, 100.0, 217.0, 300.0, 511.0])
    expected = RefractedAngleSineModel(reference_pixel=217.0, **PLAIN_PARAMETERS)(pixels)
    model = RefractedAngleSineModel(reference_pixel=217.0 * reference_pixel_unit, **parameters)

    result = model(pixels * pixel_unit)

    assert_allclose(u.Quantity(result).to_value(u.one), expected, rtol=1e-12)


# Parameter sets used to check the pixel <-> wavelength relation in both
# directions: every PV term set, and only PV0-PV2 as ViSP writes them.
ALL_GRISM_TERMS = {
    "reference_pixel": 217.0,
    "reference_wavelength": 854.1738582455826 * u.nm,
    "dispersion": 0.0022975580183395555 * u.nm / u.pix,
    "groove_density": 23000.0 / u.m,
    "spectral_order": 90,
    "incident_angle": 65.696 * u.deg,
    "refractive_index": 1.25,
    "refractive_index_derivative": 1000.0 / u.m,
    "out_of_plane_angle": 1.5 * u.deg,
    "camera_angle": 0.8 * u.deg,
}
GRATING_ONLY = {
    "reference_pixel": 500.0,
    "reference_wavelength": 589.6 * u.nm,
    "dispersion": 0.0013 * u.nm / u.pix,
    "groove_density": 316000.0 / u.m,
    "spectral_order": 10,
    "incident_angle": 73.1 * u.deg,
    # Identity-valued grism terms, as build_grating_spectral_transform passes
    # when a header only has PV0-PV2.
    "refractive_index": 1,
    "refractive_index_derivative": 0 / u.m,
    "out_of_plane_angle": 0 * u.deg,
    "camera_angle": 0 * u.deg,
}
GRISM_PARAMETER_SETS = [
    pytest.param(ALL_GRISM_TERMS, id="all_grism_terms"),
    pytest.param(GRATING_ONLY, id="grating_only"),
]


@pytest.mark.parametrize("params", GRISM_PARAMETER_SETS)
def test_pixel_from_grism_wavelength_inverts_transform(params):
    """
    Given: a grating spectral transform built from Quantity parameters
    When: pixels are mapped to wavelength and back through PixelFromGrismWavelength
    Then: the original pixels are recovered, in u.pix
    """
    transform = build_grating_spectral_transform(**params)
    inverse = PixelFromGrismWavelength(**params)
    pixels = np.array([0.0, 100.0, 217.0, 300.0, 511.0, 999.0]) * u.pix

    recovered = inverse(transform(pixels))

    assert recovered.unit == u.pix
    assert u.allclose(recovered, pixels, atol=1e-8 * u.pix)


def test_pixel_from_grism_wavelength_reference_wavelength_maps_to_reference_pixel():
    """
    Given: a PixelFromGrismWavelength model
    When: it is evaluated at the reference wavelength
    Then: it returns the reference pixel
    """
    inverse = PixelFromGrismWavelength(**ALL_GRISM_TERMS)

    result = inverse(ALL_GRISM_TERMS["reference_wavelength"])

    assert u.allclose(result, ALL_GRISM_TERMS["reference_pixel"] * u.pix)


def test_pixel_from_grism_wavelength_bare_numbers():
    """
    Given: forward and inverse grism models built from plain numbers (lengths in m, angles in rad)
    When: wavelengths from the forward relation are passed to PixelFromGrismWavelength
    Then: the original pixels are recovered as plain numbers
    """
    params = {
        "reference_pixel": 10,
        "reference_wavelength": 5e-7,
        "dispersion": 1e-12,
        "groove_density": 2e6,
        "spectral_order": 1,
        "incident_angle": np.pi / 6,
    }
    alpha_out = RefractedAngleSineModel(**params)
    to_wavelength = WavelengthFromGrismEquation(groove_density=2e6, spectral_order=1, reference_wavelength=5e-7)
    pixels = np.array([0.0, 10.0, 20.0, 500.0])
    wavelengths = to_wavelength(np.sin(np.pi / 6), alpha_out(pixels))

    recovered = PixelFromGrismWavelength(**params)(wavelengths)

    assert not isinstance(recovered, u.Quantity)
    assert_allclose(recovered, pixels, atol=1e-8)


def test_pixel_from_grism_wavelength_unphysical_wavelength_is_nan():
    """
    Given: a PixelFromGrismWavelength model
    When: it is evaluated at a wavelength with no physical refracted ray
    Then: it returns NaN rather than raising or warning
    """
    inverse = PixelFromGrismWavelength(**ALL_GRISM_TERMS)

    result = inverse([854.17, 5000.0] * u.nm)

    assert np.isfinite(result[0])
    assert np.isnan(result[1])
