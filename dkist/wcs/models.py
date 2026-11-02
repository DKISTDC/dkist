from abc import ABC
from collections.abc import Iterable
from itertools import product
from typing import Literal

import numpy as np

try:
    from numpy.typing import ArrrayLike  # NOQA
except ImportError:
    ArrayLike = Iterable

import astropy.modeling.models as m
import astropy.units as u
from astropy.modeling import CompoundModel, Model, Parameter, separable
from astropy.utils.decorators import deprecated_renamed_argument

from dkist.utils.decorators import deprecated
from dkist.utils.exceptions import DKISTDeprecationWarning

__all__ = [
    "AsymmetricMapping",
    "BaseVaryingCelestialTransform",
    "CoupledCompoundModel",
    "InverseVaryingCelestialTransform",
    "InverseVaryingCelestialTransform2D",
    "InverseVaryingCelestialTransform3D",
    "Ravel",
    "RefractedAngleSineModel",
    "Unravel",
    "VaryingCelestialTransform",
    "VaryingCelestialTransform2D",
    "VaryingCelestialTransform3D",
    "WavelengthFromGrismEquation",
    "build_grating_spectral_transform",
    "generate_celestial_transform",
    "varying_celestial_transform_from_tables",
]


# --- FITS -GRA/-GRI grism models ------------------------------------------------
# These implement the FITS grating/grism spectral-coordinate formalism of
# Greisen et al. (2006), sections 5.1.2 and 5.2:
# https://scixplorer.org/abs/2006A%26A...446..747G/abstract


def _grating_term(groove_density, spectral_order):
    return groove_density * spectral_order


def _grism_constant(groove_density, spectral_order, out_of_plane_angle):
    return _grating_term(groove_density, spectral_order) / np.cos(out_of_plane_angle)


def _reference_refracted_angle(
    groove_density,
    spectral_order,
    reference_wavelength,
    incident_angle,
    refractive_index,
    out_of_plane_angle,
):
    grism_constant = _grism_constant(groove_density, spectral_order, out_of_plane_angle)
    arcsin_argument = (
        grism_constant * reference_wavelength
    ) - refractive_index * np.sin(incident_angle)
    arcsin_argument_value = u.Quantity(arcsin_argument, copy=False).to_value(u.one)
    if np.any((arcsin_argument_value < -1) | (arcsin_argument_value > 1)):
        raise ValueError(
            "The refracted-angle sine argument is outside the valid arcsin "
            "domain [-1, 1]. Check the supplied grating/grism parameters."
        )
    return np.arcsin(arcsin_argument)


def _adjusted_grating_terms(
    alpha_in,
    groove_density,
    spectral_order,
    reference_wavelength,
    refractive_index,
    refractive_index_derivative,
    out_of_plane_angle,
):
    adjusted_incident_angle_sine = (
        refractive_index - refractive_index_derivative * reference_wavelength
    ) * alpha_in
    dispersion_denominator = (
        _grism_constant(groove_density, spectral_order, out_of_plane_angle)
        - refractive_index_derivative * alpha_in
    )
    return adjusted_incident_angle_sine, dispersion_denominator


def _validate_dispersion_denominator(dispersion_denominator, *, atol: float = 1e-15):
    if isinstance(dispersion_denominator, u.Quantity):
        denominator_value = dispersion_denominator.to_value(1 / u.m)
    else:
        denominator_value = np.asarray(dispersion_denominator)
    if np.any(np.isclose(denominator_value, 0.0, atol=atol, rtol=0.0)):
        raise ValueError(
            "The grism dispersion denominator is too close to zero, which "
            "would destabilize the wavelength solution. Check the supplied "
            "grating/grism parameters."
        )


class _GrismEquationBase(Model):
    """
    Internal base class for FITS ``-GRA``/``-GRI`` grating-coordinate models.

    This centralizes the grating/grism parameters shared by
    `RefractedAngleSineModel` and `WavelengthFromGrismEquation` so the
    parameter definitions stay consistent between the two models.
    """

    groove_density = Parameter(default=1, description="Grating ruling density.")
    spectral_order = Parameter(default=1, description="Spectral order.")
    reference_wavelength = Parameter(default=0, description="Reference wavelength.")
    refractive_index = Parameter(default=1, description="Refractive index.")
    refractive_index_derivative = Parameter(
        default=0,
        description="Derivative of refractive index with respect to wavelength.",
    )
    out_of_plane_angle = Parameter(default=0, description="Out-of-plane grating angle.")


class RefractedAngleSineModel(_GrismEquationBase):
    r"""
    Compute the sine of the refracted angle for FITS ``-GRA``/``-GRI`` spectra.

    Given a pixel coordinate, converts it to a wavelength offset from the
    reference pixel, computes the corresponding refracted angle via the grating
    geometry, and returns its sine, suitable for feeding directly into
    `~dkist.wcs.models.WavelengthFromGrismEquation`.

    In terms of the FITS grism formalism of Greisen et al. (2006), this model
    computes

    .. math::

        \alpha_{out} = \sin\left(
            \arctan\left(
                -\tan \theta + (\lambda - \lambda_r)\frac{d\Gamma}{d\lambda}
            \right)
            + \gamma_r + \theta
        \right),

    where :math:`\lambda - \lambda_r` is the wavelength offset inferred from
    the pixel coordinate using the supplied dispersion. See Greisen et al.
    (2006), especially Eqs. (77), (82), and (83).

    Parameters may be given as plain numbers or as `~astropy.units.Quantity`
    objects, but not a mixture of the two. Plain numbers must use one consistent
    length unit for every length-dependent parameter, and radians for angles.

    Parameters
    ----------
    reference_pixel : float
        Pixel coordinate of the reference point (0-indexed).
    reference_wavelength : float or `~astropy.units.Quantity`, optional
        Wavelength at the reference pixel, in units of length. Defaults to ``0``.
    dispersion : float or `~astropy.units.Quantity`, optional
        Wavelength dispersion per pixel, in units of length per pixel.
        Defaults to ``0``.
    groove_density : float or `~astropy.units.Quantity`, optional
        Grating ruling density, in units of 1/length. Defaults to ``1``.
    spectral_order : float or `~astropy.units.Quantity`, optional
        Spectral order. Dimensionless. Defaults to ``1``.
    incident_angle : float or `~astropy.units.Quantity`, optional
        Incident grating angle, in radians if a plain number. Defaults to ``0``.
    refractive_index : float or `~astropy.units.Quantity`, optional
        Refractive index at the reference wavelength. Dimensionless.
        Defaults to ``1``.
    refractive_index_derivative : float or `~astropy.units.Quantity`, optional
        Derivative of refractive index with respect to wavelength, in units of
        1/length. Defaults to ``0``.
    out_of_plane_angle : float or `~astropy.units.Quantity`, optional
        Out-of-plane grating angle, in radians if a plain number. Defaults to ``0``.
    camera_angle : float or `~astropy.units.Quantity`, optional
        Camera angle, in radians if a plain number. Defaults to ``0``.
    """

    _separable = False
    linear = False

    n_inputs = 1
    n_outputs = 1

    reference_pixel = Parameter(default=0, description="Reference pixel (0-indexed).")
    dispersion = Parameter(default=0, description="Wavelength dispersion per pixel.")
    incident_angle = Parameter(default=0, description="Incident grating angle.")
    camera_angle = Parameter(default=0, description="Camera angle.")

    def __init__(
        self,
        reference_pixel: float = 0,
        reference_wavelength: float | u.Quantity = 0,
        dispersion: float | u.Quantity = 0,
        groove_density: float | u.Quantity = 1,
        spectral_order: float | u.Quantity = 1,
        incident_angle: float | u.Quantity = 0,
        refractive_index: float | u.Quantity = 1,
        refractive_index_derivative: float | u.Quantity = 0,
        out_of_plane_angle: float | u.Quantity = 0,
        camera_angle: float | u.Quantity = 0,
        **kwargs,
    ) -> None:
        super().__init__(
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
            **kwargs,
        )
        self.inputs = ("pixel",)
        self.outputs = ("alpha_out",)

    @staticmethod
    def _grism_parameter_per_wavelength(
        groove_density,
        spectral_order,
        reference_wavelength,
        incident_angle,
        refractive_index,
        refractive_index_derivative,
        out_of_plane_angle,
        camera_angle,
    ):
        reference_refracted_angle = _reference_refracted_angle(
            groove_density,
            spectral_order,
            reference_wavelength,
            incident_angle,
            refractive_index,
            out_of_plane_angle,
        )
        grism_parameter_per_wavelength = (
            _grism_constant(groove_density, spectral_order, out_of_plane_angle)
            - refractive_index_derivative * np.sin(incident_angle)
        ) / (np.cos(reference_refracted_angle) * np.cos(camera_angle) ** 2)
        return reference_refracted_angle, grism_parameter_per_wavelength

    @staticmethod
    def _wavelength_offset(pixel, reference_pixel, dispersion):
        pixel_offset = pixel - reference_pixel
        if isinstance(dispersion, u.Quantity):
            pixel_offset = pixel_offset * u.pix
        return pixel_offset * dispersion

    @staticmethod
    def evaluate(
        pixel,
        groove_density,
        spectral_order,
        reference_wavelength,
        refractive_index,
        refractive_index_derivative,
        out_of_plane_angle,
        reference_pixel,
        dispersion,
        incident_angle,
        camera_angle,
    ):
        (
            reference_refracted_angle,
            grism_parameter_per_wavelength,
        ) = RefractedAngleSineModel._grism_parameter_per_wavelength(
            groove_density,
            spectral_order,
            reference_wavelength,
            incident_angle,
            refractive_index,
            refractive_index_derivative,
            out_of_plane_angle,
            camera_angle,
        )
        wavelength_offset = RefractedAngleSineModel._wavelength_offset(
            pixel, reference_pixel, dispersion
        )
        output_angle = (
            np.arctan(
                -np.tan(camera_angle)
                + wavelength_offset * grism_parameter_per_wavelength
            )
            + reference_refracted_angle
            + camera_angle
        )
        return np.sin(output_angle)


class WavelengthFromGrismEquation(_GrismEquationBase):
    r"""
    Solve the FITS grism wavelength equation for the wavelength.

    This model extends the classic grating equation
    (`gwcs.spectroscopy.WavelengthFromGratingEquation`) with the
    refractive-index and out-of-plane-angle corrections needed for the FITS
    ``-GRA``/``-GRI`` spectral-coordinate formalism (Greisen et al. 2006,
    Eq. 70).

    Parameters may be given as plain numbers or as `~astropy.units.Quantity`
    objects, but not a mixture of the two. Plain numbers must use one consistent
    length unit for every length-dependent parameter, and radians for angles.

    Parameters
    ----------
    groove_density : float or `~astropy.units.Quantity`
        Grating ruling density, in units of 1/length.
    spectral_order : int or `~astropy.units.Quantity`
        Spectral order. Dimensionless.
    reference_wavelength : float or `~astropy.units.Quantity`, optional
        Wavelength at the reference pixel, in units of length. Defaults to ``0``.
    refractive_index : float or `~astropy.units.Quantity`, optional
        Refractive index at the reference wavelength. Dimensionless.
        Defaults to ``1``.
    refractive_index_derivative : float or `~astropy.units.Quantity`, optional
        Derivative of refractive index with respect to wavelength, in units of
        1/length. Defaults to ``0``.
    out_of_plane_angle : float or `~astropy.units.Quantity`, optional
        Out-of-plane grating angle, in radians if a plain number. Defaults to ``0``.
    """

    _separable = False
    linear = False

    n_inputs = 2
    n_outputs = 1

    def __init__(
        self,
        groove_density: float | u.Quantity,
        spectral_order: float | u.Quantity,
        reference_wavelength: float | u.Quantity = 0,
        refractive_index: float | u.Quantity = 1,
        refractive_index_derivative: float | u.Quantity = 0,
        out_of_plane_angle: float | u.Quantity = 0,
        **kwargs,
    ) -> None:
        super().__init__(
            groove_density=groove_density,
            spectral_order=spectral_order,
            reference_wavelength=reference_wavelength,
            refractive_index=refractive_index,
            refractive_index_derivative=refractive_index_derivative,
            out_of_plane_angle=out_of_plane_angle,
            **kwargs,
        )
        self.inputs = ("alpha_in", "alpha_out")
        self.outputs = ("wavelength",)

    @staticmethod
    def evaluate(
        alpha_in,
        alpha_out,
        groove_density,
        spectral_order,
        reference_wavelength,
        refractive_index,
        refractive_index_derivative,
        out_of_plane_angle,
    ):
        adjusted_incident_angle_sine, dispersion_denominator = _adjusted_grating_terms(
            alpha_in,
            groove_density,
            spectral_order,
            reference_wavelength,
            refractive_index,
            refractive_index_derivative,
            out_of_plane_angle,
        )
        _validate_dispersion_denominator(dispersion_denominator)
        return (adjusted_incident_angle_sine + alpha_out) / dispersion_denominator

    @property
    def return_units(self):
        if self.groove_density.unit is None:
            return None
        return {"wavelength": u.Unit(1 / self.groove_density.unit)}


def build_grating_spectral_transform(
    reference_pixel: float,
    reference_wavelength: u.Quantity,
    dispersion: u.Quantity,
    groove_density: u.Quantity,
    spectral_order: u.Quantity,
    incident_angle: u.Quantity,
    refractive_index: u.Quantity = 1 * u.one,
    refractive_index_derivative: u.Quantity = 0 / u.m,
    out_of_plane_angle: u.Quantity = 0 * u.deg,
    camera_angle: u.Quantity = 0 * u.deg,
) -> CompoundModel:
    """
    Build a FITS grating spectral transform from header-derived parameters.

    Composes a constant incident-angle sine term (`~astropy.modeling.models.Const1D`),
    a pixel-dependent refracted-angle sine model
    (`~dkist.wcs.models.RefractedAngleSineModel`), and
    `~dkist.wcs.models.WavelengthFromGrismEquation`, following the FITS
    grating/grism spectral-coordinate formalism described by Greisen et al.
    (2006). The input and output angles are computed from the Greisen
    relations within the component models:
    https://scixplorer.org/abs/2006A%26A...446..747G/abstract
    """
    model = WavelengthFromGrismEquation(
        groove_density=groove_density,
        spectral_order=spectral_order,
        reference_wavelength=reference_wavelength,
        refractive_index=refractive_index,
        refractive_index_derivative=refractive_index_derivative,
        out_of_plane_angle=out_of_plane_angle,
    )

    alpha_in = m.Const1D(amplitude=np.sin(incident_angle))

    alpha_out = RefractedAngleSineModel(
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

    return m.Mapping((0, 0)) | (alpha_in & alpha_out) | model


def _round_half_up(values):
    """Round to the nearest integer, with halves going to the later pixel."""
    return np.array(np.floor(np.add(values, 0.5)), dtype=int)


def generate_celestial_transform(
        crpix: Iterable[float] | u.Quantity,
        cdelt: Iterable[float] | u.Quantity,
        pc: ArrayLike | u.Quantity,
        crval: Iterable[float] | u.Quantity,
        lon_pole: float | u.Quantity = None,
        projection: Model = m.Pix2Sky_TAN(),
) -> CompoundModel:
    """
    Create a simple celestial transform from FITS like parameters.

    Supports unitful or unitless parameters, but if any parameters have units
    all must have units, if parameters are unitless they are assumed to be in
    degrees.

    Parameters
    ----------
    crpix
        The reference pixel (a length two array).
    cdelt
        The sample interval along the pixel axis
    pc
        The rotation matrix for the affine transform. If specifying parameters
        with units this should have celestial (``u.deg``) units.
    crval
        The world coordinate at the reference pixel (a length two array).
    lon_pole
        The longitude of the celestial pole, defaults to 180 degrees.
    projection
        The map projection to use, defaults to ``TAN``.

    Notes
    -----

    This function has not been tested with more complex projections. Ensure
    that your lon_pole is correct for your projection.
    """
    spatial_unit = None
    if hasattr(crval[0], "unit"):
        spatial_unit = crval[0].unit
    # TODO: Note this assumption is only valid for certain projections.
    if lon_pole is None:
        lon_pole = 180
    if spatial_unit is not None:
        # Lon pole should always have the units of degrees
        lon_pole = u.Quantity(lon_pole, unit=u.deg)

    # Make translation unitful if all parameters have units
    translation = (0, 0)
    if spatial_unit is not None:
        translation *= pc.unit
        # If we have units then we need to convert all things to Quantity
        # as they might be Parameter classes
        crpix = u.Quantity(crpix)
        cdelt = u.Quantity(cdelt)
        crval = u.Quantity(crval)
        lon_pole = u.Quantity(lon_pole)
        pc = u.Quantity(pc)

    shift = m.Shift(-crpix[0]) & m.Shift(-crpix[1])
    scale = m.Multiply(cdelt[0]) & m.Multiply(cdelt[1])
    rot = m.AffineTransformation2D(pc, translation=translation)
    skyrot = m.RotateNative2Celestial(crval[0], crval[1], lon_pole)
    return shift | rot | scale | projection | skyrot


def update_celestial_transform_parameters(
        transform,
        crpix: Iterable[float] | u.Quantity,
        cdelt: Iterable[float] | u.Quantity,
        pc: ArrayLike | u.Quantity,
        crval: Iterable[float] | u.Quantity,
        lon_pole: float | u.Quantity,
) -> CompoundModel:
    """
    Update an existing transform with new parameter values.

    .. warning::
        This assumes that the type (quantity vs not quantity) and units of the
        new parameters are valid for the model.

    Parameters
    ----------
    crpix
        The reference pixel (a length two array).
    cdelt
        The sample interval along the pixel axis
    pc
        The rotation matrix for the affine transform. If specifying parameters
        with units this should have celestial (``u.deg``) units.
    crval
        The world coordinate at the reference pixel (a length two array).
    lon_pole
        The longitude of the celestial pole, defaults to 180 degrees.
    """
    new_params = [
        -crpix[0],
        -crpix[1],
        pc,
        transform[2].translation.quantity if hasattr(pc, "unit") else transform[2].translation.value,
        cdelt[0],
        cdelt[1],
        crval[0],
        crval[1],
        lon_pole
    ]

    for name, val in zip(transform.param_names, new_params):
        setattr(transform, name, val)

    return transform


class BaseVaryingCelestialTransform(Model, ABC):
    """
    Shared components between the forward and reverse varying celestial transforms.
    """

    # This prevents Model from broadcasting the parameters to the inputs
    standard_broadcasting = False
    _separable = False
    _input_units_allow_dimensionless = True
    _input_units_strict = True
    _is_inverse = False

    cdelt = Parameter()
    lon_pole = Parameter(default=180)

    n_outputs = 2

    @staticmethod
    def _validate_table_shapes(pc_table, crval_table, crpix_table):
        table_shape = None
        if pc_table.shape != (2, 2):
            if pc_table.shape[-2:] != (2, 2):
                raise ValueError("The pc table should be an array of 2x2 matrices.")
            table_shape = pc_table.shape[:-2]

        for table, table_name in ((crval_table, "crval"), (crpix_table, "crpix")):
            if table.shape != (2,):
                if table.shape[-1] != 2:
                    raise ValueError(f"The {table_name} table should be an array of coordinate "
                                     "pairs (the last dimension should have length 2).")

                if table_shape is not None:
                    if table_shape != table.shape[:-1]:
                        raise ValueError("The shape of the pc, crval and crpix tables should match. "
                                        f"The pc table has shape {table_shape} and the "
                                        f"{table_name} table has shape {table.shape[:-1]}")
                table_shape = table.shape[:-1]

        if pc_table.shape == (2, 2):
            pc_table = np.broadcast_to(pc_table, [*list(table_shape), 2, 2], subok=True)
        if crval_table.shape == (2,):
            crval_table = np.broadcast_to(crval_table, [*list(table_shape), 2], subok=True)
        if crpix_table.shape == (2,):
            crpix_table = np.broadcast_to(crpix_table, [*list(table_shape), 2], subok=True)

        return table_shape, pc_table, crval_table, crpix_table

    @staticmethod
    def sanitize_index(ind):
        if isinstance(ind, u.Quantity):
            ind = ind.value
        # A lookup halfway between two rows uses the later row.
        return np.array(_round_half_up(ind), dtype=int)

    @deprecated_renamed_argument("crpix", "crpix_table", "1.12", warning_type=DKISTDeprecationWarning)
    def __init__(self, *args, crval_table=None, pc_table=None, crpix_table=None, projection=m.Pix2Sky_TAN(), **kwargs):
        super().__init__(*args, **kwargs)
        (
            self.table_shape,
            self.pc_table,
            self.crval_table,
            self.crpix_table
        ) = self._validate_table_shapes(np.asanyarray(pc_table), np.asanyarray(crval_table), np.asanyarray(crpix_table))

        if not isinstance(projection, m.Pix2SkyProjection):
            raise TypeError("The projection keyword should be a Pix2SkyProjection model class.")
        self.projection = projection

        if self._is_inverse:
            self.inputs = ("lon", "lat", "z", "q", "m")[:self.n_inputs]
            self.outputs = ("x", "y")
        else:
            self.inputs = ("x", "y", "z", "q", "m")[:self.n_inputs]
            self.outputs = ("lon", "lat")

        if len(self.table_shape) != self.n_inputs-2:
            raise ValueError(f"This model can only be constructed with a {self.n_inputs-2}-dimensional lookup table.")

        self._transform = generate_celestial_transform(
            crpix=[0, 0],
            cdelt=[1, 1],
            pc=np.identity(2),
            crval=[0, 0],
            lon_pole=180,
            projection=projection,
        )

    @property
    @deprecated(since="1.12", alternative="crpix_table")
    def crpix(self):
        return self.crpix_table

    def transform_at_index(self, ind, cdelt=None, lon_pole=None):
        """
        Generate a spatial model based on an index for the pc and crval tables.

        Parameters
        ----------
        zind : int
          The index to the lookup table.

        **kwargs
          The keyword arguments are optional and if not specified will be read
          from the parameters to this model.

        Returns
        -------
        `astropy.modeling.CompoundModel`

        """
        # If we are out of bounds of the lookup table return a constant model
        fill_val = np.nan
        if (np.array(ind) > np.array(self.table_shape) - 1).any() or (np.array(ind) < 0).any():
            return m.Const1D(fill_val) & m.Const1D(fill_val)

        # The self._transform is always unitless and always in degrees.
        # So we need to strip down the parameters to be in the correct units

        # If we are being called from inside evaluate we can skip the lookup
        # but we have to handle both dimensionless and unitful parameters
        if cdelt is None:
            if self.cdelt.unit is not None:
                cdelt = u.Quantity(self.cdelt)
            else:
                cdelt = self.cdelt.value
        if lon_pole is None:
            if self.lon_pole.unit is not None:
                lon_pole = u.Quantity(self.lon_pole)
            else:
                lon_pole = self.lon_pole.value

        if isinstance(self.pc_table, u.Quantity):
            pc = self.pc_table[ind].to_value(u.pix)
        else:
            pc = self.pc_table[ind]

        if isinstance(self.crval_table, u.Quantity):
            crval = self.crval_table[ind].to_value(u.deg)
        else:
            crval = self.crval_table[ind]

        if isinstance(self.crpix_table, u.Quantity):
            crpix = self.crpix_table[ind].to_value(u.pix)
        else:
            crpix = self.crpix_table[ind]

        if isinstance(cdelt, u.Quantity):
            cdelt = cdelt.to_value(u.deg / u.pix)

        if isinstance(lon_pole, u.Quantity):
            lon_pole = lon_pole.to_value(u.deg)

        return update_celestial_transform_parameters(
            self._transform,
            crpix=crpix,
            cdelt=cdelt,
            pc=pc,
            crval=crval,
            lon_pole=lon_pole,
        )

    def _map_transform(self, *arrays, cdelt, lon_pole, inverse=False):
        # We need to broadcast the arrays together so they are all the same shape
        barrays = np.broadcast_arrays(*arrays, subok=True)
        # # Convert the z, q, and m coordinates where present into indices to the lookup tables
        inds = []
        for barray, size in zip(barrays[2:], self.table_shape):
            ind = self.sanitize_index(barray)
            # Keep the outer pixel edge, size - 0.5, on the last row.
            value = barray.value if isinstance(barray, u.Quantity) else barray
            inds.append(np.where(value <= size - 0.5, np.minimum(ind, size - 1), ind))

        if isinstance(barrays[0], u.Quantity):
            # Because we have set input_units_strict to True we can assume that
            # all inputs have the correct units for the transform
            arrays = [arr.value for arr in barrays]
        else:
            arrays = barrays

        x_out = np.full_like(arrays[0], np.nan)
        y_out = np.full_like(arrays[1], np.nan)

        # We now loop over every unique value of z and compute the transform.
        # This means we make the minimum number of calls possible to the transform.
        ranges = [np.unique(ind) for ind in inds]
        for ind in product(*ranges):
            # Leave points outside the lookup table as NaN.
            if any(i < 0 or i >= size for i, size in zip(ind, self.table_shape)):
                continue
            # Scalar parameters are reshaped to be length one arrays by modeling
            sct = self.transform_at_index(ind, cdelt=cdelt[0], lon_pole=lon_pole[0])

            # Call this transform for all values of x, y where z == zind
            masks = [inds[i] == ind[i] for i in range(len(ind))]
            mask = np.logical_and.reduce(masks)
            if inverse:
                xx, yy = sct.inverse(arrays[0][mask], arrays[1][mask])
            else:
                xx, yy = sct(arrays[0][mask], arrays[1][mask])

            x_out[mask], y_out[mask] = xx, yy

        # Put the units back if we started with some
        if isinstance(barrays[0], u.Quantity):
            if self._is_inverse:
                x_out = x_out << u.pix
                y_out = y_out << u.pix
            else:
                x_out = x_out << u.deg
                y_out = y_out << u.deg

        return x_out, y_out

    def evaluate(self, *inputs):
        # This method has to be able to take an arbitrary number of arrays but also accept not being given kwargs
        # Fortunately we know how many arrays to expect from the number of inputs
        # Anything extra is therefore a kwarg
        arrays = inputs[:self.n_inputs]
        kwargs = inputs[self.n_inputs:]
        keys = ["cdelt", "lon_pole"]
        kwargs = dict(zip(keys, kwargs))
        return self._map_transform(*arrays, inverse=self._is_inverse, **kwargs)

    @property
    def input_units(self):
        # NB: x and y are normally on the detector and z is typically the number of raster steps
        if self._is_inverse:
            dims = ["z", "q", "m"]
            dict.fromkeys(dims[:self.n_inputs], u.pix)
            units = {"lon": u.deg, "lat": u.deg}
            for d in dims[:self.n_inputs-2]:
                units[d] = u.pix
            return units

        dims = ["x", "y", "z", "q", "m"]
        return dict.fromkeys(dims[:self.n_inputs], u.pix)


class VaryingCelestialTransform(BaseVaryingCelestialTransform):
    """
    A celestial transform which can vary its pointing and rotation with time.

    This model stores a lookup table for the reference pixel ``crval_table``
    and the rotation matrix ``pc_table`` which are indexed with a third pixel
    index (z).

    The other parameters (``crpix``, ``cdelt``, and ``lon_pole``) are fixed.
    """
    n_inputs = 3

    @property
    def inverse(self):
        return InverseVaryingCelestialTransform(
            crpix_table=self.crpix_table,
            cdelt=self.cdelt,
            lon_pole=self.lon_pole,
            pc_table=self.pc_table,
            crval_table=self.crval_table,
            projection=self.projection,
        )


class VaryingCelestialTransform2D(BaseVaryingCelestialTransform):
    n_inputs = 4

    @property
    def inverse(self):
        return InverseVaryingCelestialTransform2D(
            crpix_table=self.crpix_table,
            cdelt=self.cdelt,
            lon_pole=self.lon_pole,
            pc_table=self.pc_table,
            crval_table=self.crval_table,
            projection=self.projection,
        )


class VaryingCelestialTransform3D(BaseVaryingCelestialTransform):
    n_inputs = 5

    @property
    def inverse(self):
        return InverseVaryingCelestialTransform3D(
            crpix_table=self.crpix_table,
            cdelt=self.cdelt,
            lon_pole=self.lon_pole,
            pc_table=self.pc_table,
            crval_table=self.crval_table,
            projection=self.projection,
        )


class InverseVaryingCelestialTransform(BaseVaryingCelestialTransform):
    n_inputs = 3
    _is_inverse = True

class InverseVaryingCelestialTransform2D(BaseVaryingCelestialTransform):
    n_inputs = 4
    _is_inverse = True


class InverseVaryingCelestialTransform3D(BaseVaryingCelestialTransform):
    n_inputs = 5
    _is_inverse = True


class CoupledCompoundModel(CompoundModel):
    """
    This class takes two models which share one or more inputs on the forward
    transform, and where the left hand model's inverse is dependent on the
    output of the right hand model's inverse output.

    Parameters
    ----------
    op : `str`
        The operator to use, can only be ``'&'``.
    left : `astropy.modeling.Model`
        The left hand model, should have one or more inputs which are shared
        with the right hand model on the forward transform, and also rely on
        these inputs for the inverse transform.
    right : `astropy.modeling.Model`
        The right hand model, no special behaviour is required here.
    shared_inputs : `int`
        The number of inputs (counted from the end of the end of the inputs to
        the left model and the start of the inputs to the right model) which
        are shared between the two models.

    Example
    -------

    Take the following example with a time dependent celestial transform
    (modelled as dependent upon the pixel coordinate for time rather than the
    world coordinate).

    The forward transform uses the "z" pixel dimension as input to both the
    Celestial and Temporal models, this leads to the following transform in the
    forward direction::

        x  y           z
        │  │           │
        │  │  ┌────────┤
        │  │  │        │
        ▼  ▼  ▼        ▼
      ┌─────────┐  ┌────────┐
      │Celestial│  │Temporal│
      └─┬───┬───┘  └───┬────┘
        │   │          │
        │   │          │
        │   │          │
        ▼   ▼          ▼
       lon lat       time

    This could trivially be reproduced using `~astropy.modeling.models.Mapping`.

    The complexity is in the reverse transform, where the inverse Celestial
    transform is also dependent upon the pixel coordinate z.
    This means that the output of the inverse Temporal transform has to be
    duplicated as an input to the Celestial transform's inverse.
    This is achieved by the use of the ``Mapping`` models in
    ``CoupledCompoundModel.inverse`` to create a multi-stage compound model
    which duplicates the output of the right hand side model::

       lon lat       time
        │   │         │
        │   │         ▼
        │   │     ┌─────────┐
        │   │     │Temporal'│
        │   │     └──┬──┬───┘
        │   │    z   │  │
        │   │  ┌─────┘  │
        │   │  │        │
        ▼   ▼  ▼        │
      ┌──────────┐      │
      │Celestial'│      │
      └─┬───┬────┘      │
        │   │           │
        ▼   ▼           ▼
        x   y           z

    """

    _separable = False

    def __init__(self, op, left, right, name=None, shared_inputs=1):
        if op != "&":
            raise ValueError(
                f"The {self.__class__.__name__} class should only be used with the & operator."
            )
        super().__init__(op, left, right, name=name)
        self.n_inputs = self.n_inputs - shared_inputs
        # The shared inputs are the ones at the end of the left model and the
        # start of the right model, so that we don't duplicate them drop the
        # ones in the right model
        self.inputs = left.inputs + right.inputs[shared_inputs:]
        self.shared_inputs = shared_inputs

    def _evaluate(self, *args, **kw):
        leftval = self.left(*(args[:self.left.n_inputs]), **kw)
        rightval = self.right(*(args[-self.right.n_inputs:]), **kw)

        return self._apply_operators_to_value_lists(leftval, rightval, **kw)

    @property
    def inverse(self):
        left_inverse = self.left.inverse
        right_inverse = self.right.inverse

        n_left_only_inputs = left_inverse.n_inputs - self.shared_inputs
        n_right_only_inputs = right_inverse.n_outputs - self.shared_inputs

        # left only inputs are pass thru
        mapping = list(range(n_left_only_inputs))
        # step1 passes through the left-only inputs and inverts the right only inputs
        step1 = m.Mapping(tuple(mapping)) & right_inverse
        # next we remap the output of step 1 and replicate the shared outputs
        shared_start = max(mapping) + 1
        shared = list(range(shared_start, shared_start + self.shared_inputs)) * 2
        right_start = max(shared) + 1
        right = list(range(right_start, right_start + n_right_only_inputs))
        inter_mapping = mapping + shared + right
        step2 = m.Mapping(tuple(inter_mapping)) | (left_inverse & m.Identity(right_inverse.n_outputs))

        return step1 | step2

    def _calculate_separability_matrix(self):
        sepleft = separable._separable(self.left)
        sepright = separable._separable(self.right)

        noutp = separable._compute_n_outputs(sepleft, sepright)

        cleft = np.zeros((noutp, sepleft.shape[1]))
        cleft[: sepleft.shape[0], : sepleft.shape[1]] = sepleft

        cright = np.zeros((noutp, sepright.shape[1]))
        cright[-sepright.shape[0]:, -sepright.shape[1]:] = sepright

        left_solo_end = self.left.n_inputs - self.shared_inputs
        right_solo_start = left_solo_end + self.shared_inputs
        matrix = np.zeros((self.n_outputs, self.n_inputs))
        matrix[:, :left_solo_end] = cleft[:, :left_solo_end]
        matrix[:, left_solo_end:right_solo_start] = np.logical_or(cleft[:, left_solo_end:],
                                                                  cright[:, :self.shared_inputs])
        matrix[:, right_solo_start:] = cright[:, self.shared_inputs:]

        return matrix


class AsymmetricMapping(m.Mapping):
    """
    A Mapping which uses a different mapping for the forward and backward directions.
    """
    def __init__(
        self,
        forward_mapping,
        backward_mapping,
        forward_n_inputs=None,
        backward_n_inputs=None,
        name=None,
        meta=None,
    ):
        super().__init__(forward_mapping, n_inputs=forward_n_inputs, name=name, meta=meta)
        self.backward_mapping = backward_mapping
        self.forward_mapping = self.mapping
        self.backward_n_inputs = backward_n_inputs
        self.forward_n_inputs = self.n_inputs

    @property
    def inverse(self):
        return type(self)(
            self.backward_mapping,
            self.forward_mapping,
            self.backward_n_inputs,
            self.forward_n_inputs,
            name=self.name
        )

    def __repr__(self):
        if self.name is None:
            return f"<AsymmetricMapping({self.mapping})>"
        return f"<AsymmetricMapping({self.mapping}, name={self.name!r})>"

varying_celestial_transform_dict = {
    # Map (num_dims, inverse) to class
    (1, False): VaryingCelestialTransform,
    (2, False): VaryingCelestialTransform2D,
    (3, False): VaryingCelestialTransform3D,
    (1, True): InverseVaryingCelestialTransform,
    (2, True): InverseVaryingCelestialTransform2D,
    (3, True): InverseVaryingCelestialTransform3D,
}

@deprecated_renamed_argument("crpix", "crpix_table", "1.10", warning_type=DKISTDeprecationWarning)
def varying_celestial_transform_from_tables(
        crpix_table: ArrayLike | u.Quantity,
        cdelt: Iterable[float] | u.Quantity,
        pc_table: ArrayLike | u.Quantity,
        crval_table: Iterable[float] | u.Quantity,
        lon_pole: float | u.Quantity = None,
        projection: Model = m.Pix2Sky_TAN(),
        inverse: bool = False,
        slit: Literal[0, 1] | None = None,
) -> BaseVaryingCelestialTransform:
    """
    Generate a `.BaseVaryingCelestialTransform` based on the dimensionality of the tables.
    """

    table_shape, pc_table, crval_table, crpix_table = BaseVaryingCelestialTransform._validate_table_shapes(
        np.asanyarray(pc_table),
        np.asanyarray(crval_table),
        np.asanyarray(crpix_table),
    )
    if (table_d := len(table_shape)) not in range(1, 4):
        raise ValueError("Only 1D, 2D and 3D lookup tables are supported.")


    cls = varying_celestial_transform_dict[(table_d, inverse)]
    transform = cls(
        crpix_table=crpix_table,
        cdelt=cdelt,
        crval_table=crval_table,
        pc_table=pc_table,
        lon_pole=lon_pole,
        projection=projection,
    )

    # For slit models we duplicate one of the spatial pixel inputs to also be
    # the lookup table input
    if slit is not None:
        if slit not in [0, 1]:
            raise ValueError("The slit dimension must be one of the first two pixel dimensions.")
        mapping = list(range(table_d + 2 - 1))
        mapping.insert(2, slit)
        backward_mapping = [[1, 0][slit]]
        transform = AsymmetricMapping(forward_mapping=mapping,
                                      backward_mapping=backward_mapping,
                                      backward_n_inputs=transform.inverse.n_outputs,
                                      name="SlitMapping") | transform
    return transform


class Ravel(Model):
    n_outputs = 1
    _separable = False
    _input_units_allow_dimensionless = True

    @property
    def n_inputs(self):
        return len(self.array_shape)

    @property
    def inputs(self):
        return self._inputs

    @inputs.setter
    def inputs(self, value):
        self._inputs = value

    @property
    def input_units(self):
        return {f"x{idx}": u.pix for idx in range(self.n_inputs)}

    @property
    def outputs(self):
        return self._outputs

    @outputs.setter
    def outputs(self, value):
        self._outputs = value

    @property
    def return_units(self):
        return {"y": u.pix}

    def __init__(self, array_shape, order="C", **kwargs):
        if len(array_shape) < 2 or np.prod(array_shape) < 1:
            raise ValueError("array_shape must be at least 2D and have values >= 1")
        self.array_shape = tuple(array_shape)
        if order not in ("C", "F"):
            raise ValueError("order kwarg must be one of 'C' or 'F'")
        self.order = order
        super().__init__(**kwargs)
        # super dunder init sets inputs and outputs to default values so set what we want here
        self.inputs = tuple([f"x{idx}" for idx in range(self.n_inputs)])
        self.outputs = "y",

    def evaluate(self, *inputs_):
        """Evaluate the forward ravel for a given tuple of pixel values."""
        if hasattr(inputs_[0], "unit"):
            has_units = True
            input_values = [item.to_value(u.pix) for item in inputs_]
        else:
            has_units = False
            input_values = inputs_
        input_values = [item.flatten() if isinstance(item, np.ndarray) else item for item in input_values]
        # round the index values, but clip them if they exceed the array bounds
        # the bounds are one less than the shape dimension value
        array_bounds = np.array(self.array_shape) - 1
        # Halfway coordinates use the later pixel. Clip the outer edge to the
        # last pixel before calculating the fractional offset.
        rounded_inputs = np.clip(_round_half_up(input_values), 0, array_bounds[:, np.newaxis])
        result = np.ravel_multi_index(rounded_inputs, self.array_shape, order=self.order, mode="clip").astype(float)
        index = 0 if self.order == "F" else -1
        # Adjust the result to allow a fractional part for interpolation in Tabular1D
        fraction = input_values[index] - rounded_inputs[index]
        result += fraction
        # Coordinates at either outer pixel edge are still inside the array.
        values = np.asarray(input_values)
        oob = ~((values >= -0.5) & (values <= array_bounds[:, np.newaxis] + 0.5)).all(axis=0)
        result[oob] = np.nan
        # Put the units back if they were there...
        if has_units:
            result = result * u.pix
        else:
            result = np.array(result)
        return result

    @property
    def inverse(self):
        return Unravel(self.array_shape, order=self.order)

    def __repr__(self):
        return f'<{self.__class__.__qualname__}(array_shape={self.array_shape}, order="{self.order}")>'


class Unravel(Model):
    n_inputs = 1
    _separable = False
    _input_units_allow_dimensionless = True

    @property
    def inputs(self):
        return self._inputs

    @inputs.setter
    def inputs(self, value):
        self._inputs = value

    @property
    def input_units(self):
        return {"x": u.pix}

    @property
    def n_outputs(self):
        return len(self.array_shape)

    @property
    def outputs(self):
        return self._outputs

    @outputs.setter
    def outputs(self, value):
        self._outputs = value

    @property
    def return_units(self):
        return {f"y{idx}": u.pix for idx in range(self.n_outputs)}

    def __init__(self, array_shape, order="C", **kwargs):
        if len(array_shape) < 2 or np.prod(array_shape) < 1:
            raise ValueError("array_shape must be at least 2D and have values >= 1")
        self.array_shape = array_shape
        if order not in ("C", "F"):
            raise ValueError("order kwarg must be one of 'C' or 'F'")
        self.order = order
        super().__init__(**kwargs)
        # super dunder init sets inputs and outputs to default values so set what we want here
        self.inputs = "x",
        self.outputs = tuple([f"y{idx}" for idx in range(self.n_outputs)])

    def evaluate(self, input_):
        """Evaluate the reverse ravel (unravel) for a given pixel value."""
        if hasattr(input_, "unit"):
            has_units = True
            input_value = [item.to_value(u.pix) for item in input_]
            input_value_int = [int(item) for item in input_value]
        else:
            has_units = False
            input_value = input_
            input_value_int = [int(item) for item in input_]

        result = list(np.unravel_index(input_value_int, self.array_shape, order=self.order))
        result = [item.astype(float) for item in result]
        # Adjust the result to allow a fractional part for interpolation in Tabular1D
        index = 0 if self.order == "F" else -1
        fraction = np.remainder(input_value, 1)
        result[index] += fraction
        if has_units:
            result = result * u.pix
        return result

    @property
    def inverse(self):
        return Ravel(self.array_shape, order=self.order)

    def __repr__(self):
        return f'<{self.__class__.__qualname__}(array_shape={self.array_shape}, order="{self.order}")>'
