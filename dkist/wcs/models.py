from typing import Any, Union, Iterable

import numpy as np

try:
    from numpy.typing import ArrrayLike  # NOQA
except ImportError:
    ArrayLike = Any

import astropy.modeling.models as m
import astropy.units as u
from astropy.modeling import CompoundModel, Model, Parameter, separable

__all__ = ['CoupledCompoundModel',
           'InverseVaryingCelestialTransform',
           'VaryingCelestialTransform',
           'BaseVaryingCelestialTransform']


def generate_celestial_transform(crpix: Union[Iterable[float], u.Quantity],
                                 cdelt: Union[Iterable[float], u.Quantity],
                                 pc: Union[ArrayLike, u.Quantity],
                                 crval: Union[Iterable[float], u.Quantity],
                                 lon_pole: Union[float, u.Quantity] = None,
                                 projection: Model = m.Pix2Sky_TAN()) -> CompoundModel:
    """
    Create a simple celestial transform from FITS like parameters.

    Supports unitful or unitless parameters, but if any parameters have units
    all must have units, if parameters are unitless they are assumed to be in
    degrees.

    Parameters
    ----------
    crpix
        The reference pixel (a length two array).
    crval
        The world coordinate at the reference pixel (a length two array).
    pc
        The rotation matrix for the affine transform. If specifying parameters
        with units this should have celestial (``u.deg``) units.
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
        lon_pole = u.Quantity(lon_pole, unit=spatial_unit)

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
    return shift | scale | rot | projection | skyrot


class BaseVaryingCelestialTransform(Model):
    """
    Shared components between the forward and reverse varying celestial transforms.
    """

    # This prevents Model from broadcasting the paramters to the inputs
    standard_broadcasting = False
    _separable = False
    _input_units_allow_dimensionless = True

    crpix = Parameter()
    cdelt = Parameter()
    lon_pole = Parameter(default=180)

    @staticmethod
    def _validate_table_shapes(pc_table, crval_table):
        table_shape = None
        if pc_table.shape != (2, 2):
            if pc_table.shape[-2:] != (2, 2):
                raise ValueError("The pc table should be an array of 2x2 matrices.")
            table_shape = pc_table.shape[:-2]

        if crval_table.shape != (2,):
            if crval_table.shape[-1] != 2:
                raise ValueError("The crval table should be an array of coordinate "
                                 "pairs (the last dimension should have length 2).")

            if table_shape is not None:
                if table_shape != crval_table.shape[:-1]:
                    raise ValueError("The shape of the pc and crval tables should match. "
                                     f"The pc table has shape {table_shape} and the "
                                     f"crval table has shape {crval_table.shape[:-1]}")
            table_shape = crval_table.shape[:-1]

        if pc_table.shape == (2, 2):
            pc_table = np.broadcast_to(pc_table, list(table_shape) + [2, 2], subok=True)
        if crval_table.shape == (2,):
            crval_table = np.broadcast_to(crval_table, list(table_shape) + [2], subok=True)

        return table_shape, pc_table, crval_table

    @staticmethod
    def sanitize_index(ind):
        if isinstance(ind, u.Quantity):
            ind = ind.value
        return np.array(np.round(ind), dtype=int)

    def __init__(self, *args, crval_table=None, pc_table=None, projection=m.Pix2Sky_TAN(), **kwargs):
        super().__init__(*args, **kwargs)

        (self.table_shape,
         self.pc_table,
         self.crval_table) = self._validate_table_shapes(np.asanyarray(pc_table),
                                                         np.asanyarray(crval_table))

        if not isinstance(projection, m.Pix2SkyProjection):
            raise TypeError("The projection keyword should be a Pix2SkyProjection model class.")
        self.projection = projection

    def transform_at_index(self, ind, crpix=None, cdelt=None, lon_pole=None):
        """
        Generate a spatial model based on an index for the pc and crval tables.

        Parameters
        ----------
        zind : int
          The index to the lookup table.Q

        **kwargs
          The keyword arguments are optional and if not specified will be read
          from the parameters to this model.

        Returns
        -------
        `astropy.modeling.CompoundModel`

        """
        # If we are being called from inside evaluate we can skip the lookup
        crpix = crpix if crpix is not None else self.crpix
        cdelt = cdelt if cdelt is not None else self.cdelt
        lon_pole = lon_pole if lon_pole is not None else self.lon_pole

        fill_val = np.nan
        if isinstance(crpix, u.Quantity):
            fill_val = np.nan * u.deg
        if (np.array(ind) > np.array(self.table_shape) - 1).any() or (np.array(ind) < 0).any():
            return m.Const1D(fill_val) & m.Const1D(fill_val)

        sct = generate_celestial_transform(crpix=crpix,
                                           cdelt=cdelt,
                                           pc=self.pc_table[ind],
                                           crval=self.crval_table[ind],
                                           lon_pole=lon_pole,
                                           projection=self.projection)

        return sct

    def _map_transform(self, x, y, z, crpix, cdelt, lon_pole, inverse=False):
        # We need to broadcast the arrays together so they are all the same shape
        bx, by, bz = np.broadcast_arrays(x, y, z, subok=True)
        # Convert the z coordinate into an index to the lookup tables
        ind = self.sanitize_index(bz)

        # Generate output arrays (ignore units for simplicity)
        if isinstance(bx, u.Quantity):
            x_out = np.empty_like(bx.value)
            y_out = np.empty_like(by.value)
        else:
            x_out = np.empty_like(bx)
            y_out = np.empty_like(by)

        # We now loop over every unique value of z and compute the transform.
        # This means we make the minimum number of calls possible to the transform.
        for zind in np.unique(ind):
            # Scalar parameters are reshaped to be length one arrays by modeling
            sct = self.transform_at_index(zind, crpix[0], cdelt[0], lon_pole[0])

            # Call this transform for all values of x, y where z == zind
            mask = ind == zind
            if inverse:
                xx, yy = sct.inverse(bx[mask], by[mask])
            else:
                xx, yy = sct(bx[mask], by[mask])

            if isinstance(xx, u.Quantity):
                x_out[mask], y_out[mask] = xx.value, yy.value
            else:
                x_out[mask], y_out[mask] = xx, yy

        # Put the units back
        if isinstance(xx, u.Quantity):
            x_out = x_out << xx.unit
            y_out = y_out << yy.unit

        return x_out, y_out


class VaryingCelestialTransform(BaseVaryingCelestialTransform):
    """
    A celestial transform which can vary it's pointing and rotation with time.

    This model stores a lookup table for the reference pixel ``crval_table``
    and the rotation matrix ``pc_table`` which are indexed with a third pixel
    index (z).

    The other parameters (``crpix``, ``cdelt``, and ``lon_pole``) are fixed.
    """
    n_inputs = 3
    n_outputs = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inputs = ("x", "y", "z")
        self.outputs = ("lon", "lat")

        if len(self.table_shape) != 1:
            raise ValueError("This model can only be constructed with a one dimensional lookup table.")

    @property
    def input_units(self):
        return {"x": u.pix, "y": u.pix, "z": u.pix}

    def evaluate(self, x, y, z, crpix, cdelt, lon_pole):
        return self._map_transform(x, y, z, crpix, cdelt, lon_pole)

    @property
    def inverse(self):
        ivct = InverseVaryingCelestialTransform(crpix=self.crpix,
                                                cdelt=self.cdelt,
                                                lon_pole=self.lon_pole,
                                                pc_table=self.pc_table,
                                                crval_table=self.crval_table,
                                                projection=self.projection)
        return ivct


class InverseVaryingCelestialTransform(BaseVaryingCelestialTransform):
    """
    The inverse of VaryingCelestialTransform.

    This inverse still depends on the pixel coordinate ``z`` to index the lookup tables.
    """
    n_inputs = 3
    n_outputs = 2

    @property
    def input_units(self):
        return {"lon": u.deg, "lat": u.deg, "z": u.pix}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inputs = ("lon", "lat", "z")
        self.outputs = ("x", "y")

    def evaluate(self, lon, lat, z, crpix, cdelt, lon_pole, **kwargs):
        return self._map_transform(lon, lat, z, crpix, cdelt, lon_pole, inverse=True)


class BaseVaryingCelestialTransform2D(BaseVaryingCelestialTransform):
    def _map_transform(self, x, y, z, q, crpix, cdelt, lon_pole, inverse=False):
        # We need to broadcast the arrays together so they are all the same shape
        bx, by, bz, bq = np.broadcast_arrays(x, y, z, q, subok=True)
        # Convert the z coordinate into an index to the lookup tables
        zind = self.sanitize_index(bz)
        qind = self.sanitize_index(bq)

        # Generate output arrays (ignore units for simplicity)
        if isinstance(bx, u.Quantity):
            x_out = np.empty_like(bx.value)
            y_out = np.empty_like(by.value)
        else:
            x_out = np.empty_like(bx)
            y_out = np.empty_like(by)

        # We now loop over every unique value of z and compute the transform.
        # This means we make the minimum number of calls possible to the transform.
        for qq in np.unique(qind):
            for zz in np.unique(zind):
                # Scalar parameters are reshaped to be length one arrays by modeling
                sct = self.transform_at_index((zz, qq), crpix[0], cdelt[0], lon_pole[0])

                # Call this transform for all values of x, y where z == zind and q == qind
                mask = np.logical_and(zind == zz, qind == qq)
                if inverse:
                    xx, yy = sct.inverse(bx[mask], by[mask])
                else:
                    xx, yy = sct(bx[mask], by[mask])

                if isinstance(xx, u.Quantity):
                    x_out[mask], y_out[mask] = xx.value, yy.value
                else:
                    x_out[mask], y_out[mask] = xx, yy

        # Put the units back
        if isinstance(xx, u.Quantity):
            x_out = x_out << xx.unit
            y_out = y_out << yy.unit

        return x_out, y_out


class VaryingCelestialTransform2D(BaseVaryingCelestialTransform2D):
    n_inputs = 4
    n_outputs = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inputs = ("x", "y", "z", "q")
        self.outputs = ("lon", "lat")

        if len(self.table_shape) != 2:
            raise ValueError("This model can only be constructed with a two dimensional lookup table.")

    @property
    def input_units(self):
        return {"x": u.pix, "y": u.pix, "z": u.pix, "q": u.pix}

    def evaluate(self, x, y, z, q, crpix, cdelt, lon_pole):
        return self._map_transform(x, y, z, q, crpix, cdelt, lon_pole)

    @property
    def inverse(self):
        ivct = InverseVaryingCelestialTransform2D(crpix=self.crpix,
                                                  cdelt=self.cdelt,
                                                  lon_pole=self.lon_pole,
                                                  pc_table=self.pc_table,
                                                  crval_table=self.crval_table,
                                                  projection=self.projection)
        return ivct


class InverseVaryingCelestialTransform2D(BaseVaryingCelestialTransform2D):
    n_inputs = 4
    n_outputs = 2

    @property
    def input_units(self):
        return {"lon": u.deg, "lat": u.deg, "z": u.pix, "q": u.pix}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inputs = ("lon", "lat", "z", "q")
        self.outputs = ("x", "y")

    def evaluate(self, lon, lat, z, q, crpix, cdelt, lon_pole, **kwargs):
        return self._map_transform(lon, lat, z, q, crpix, cdelt, lon_pole,
                                   inverse=True)


class BaseVaryingCelestialTransformSlit(BaseVaryingCelestialTransform):
    def _map_transform(self, x, y, crpix, cdelt, lon_pole, inverse=False):
        # We need to broadcast the arrays together so they are all the same shape
        bx, by = np.broadcast_arrays(x, y, subok=True)
        # Convert the z coordinate into an index to the lookup tables
        yind = self.sanitize_index(by)

        # Generate output arrays (ignore units for simplicity)
        if isinstance(bx, u.Quantity):
            x_out = np.empty_like(bx.value)
            y_out = np.empty_like(by.value)
        else:
            x_out = np.empty_like(bx)
            y_out = np.empty_like(by)

        # We now loop over every unique value of y and compute the transform.
        # This means we make the minimum number of calls possible to the transform.
        for yyind in np.unique(yind):
            # Scalar parameters are reshaped to be length one arrays by modeling
            sct = self.transform_at_index(yyind, crpix[0], cdelt[0], lon_pole[0])

            # Call this transform for all values of x, y where y == yind
            mask = yind == yyind
            if inverse:
                # Note this isn't use as the inverse of this model uses the
                # standard 2D inverse.
                xx, yy = sct.inverse(bx[mask], by[mask])  # pragma: no cover
            else:
                xx, yy = sct(bx[mask], by[mask])

            if isinstance(xx, u.Quantity):
                x_out[mask], y_out[mask] = xx.value, yy.value
            else:
                x_out[mask], y_out[mask] = xx, yy

        # Put the units back
        if isinstance(xx, u.Quantity):
            x_out = x_out << xx.unit
            y_out = y_out << yy.unit

        return x_out, y_out


class VaryingCelestialTransformSlit(BaseVaryingCelestialTransformSlit):
    n_inputs = 2
    n_outputs = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inputs = ("slity", "raster")
        self.outputs = ("lon", "lat")

        if len(self.table_shape) != 1:
            raise ValueError("This model can only be constructed with a one dimensional lookup table.")

    @property
    def input_units(self):
        return {"slity": u.pix, "raster": u.pix}

    def evaluate(self, slity, raster, crpix, cdelt, lon_pole):
        return self._map_transform(slity, raster, crpix, cdelt, lon_pole)

    @property
    def inverse(self):
        ivct = InverseVaryingCelestialTransformSlit(crpix=self.crpix,
                                                    cdelt=self.cdelt,
                                                    lon_pole=self.lon_pole,
                                                    pc_table=self.pc_table,
                                                    crval_table=self.crval_table,
                                                    projection=self.projection)
        return ivct


class InverseVaryingCelestialTransformSlit(BaseVaryingCelestialTransform):
    n_inputs = 3
    n_outputs = 1

    @property
    def input_units(self):
        return {"lon": u.deg, "lat": u.deg, "raster": u.pix}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inputs = ("lon", "lat", "raster")
        self.outputs = ("slit-y",)

    def evaluate(self, lon, lat, y, crpix, cdelt, lon_pole, **kwargs):
        return self._map_transform(lon, lat, y, crpix, cdelt, lon_pole,
                                   inverse=True)[0]


class VaryingCelestialTransformSlit2D(BaseVaryingCelestialTransform):
    n_inputs = 3
    n_outputs = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inputs = ("slity", "raster", "repeat")
        self.outputs = ("lon", "lat")

        if len(self.table_shape) != 2:
            raise ValueError("This model can only be constructed with a two dimensional lookup table.")

    @property
    def input_units(self):
        return {"slity": u.pix, "raster": u.pix, "repeat": u.pix}

    def evaluate(self, slity, raster, repeat, crpix, cdelt, lon_pole):
        return self._map_transform(slity, raster, repeat, crpix, cdelt, lon_pole)

    @property
    def inverse(self):
        ivct = InverseVaryingCelestialTransformSlit2D(crpix=self.crpix,
                                                      cdelt=self.cdelt,
                                                      lon_pole=self.lon_pole,
                                                      pc_table=self.pc_table,
                                                      crval_table=self.crval_table,
                                                      projection=self.projection)
        return ivct

    def _map_transform(self, x, y, z, crpix, cdelt, lon_pole, inverse=False):
        # We need to broadcast the arrays together so they are all the same shape
        bx, by, bz = np.broadcast_arrays(x, y, z, subok=True)
        # Convert the z coordinate into an index to the lookup tables
        zind = self.sanitize_index(bz)
        yind = self.sanitize_index(by)

        # Generate output arrays (ignore units for simplicity)
        if isinstance(bx, u.Quantity):
            x_out = np.empty_like(bx.value)
            y_out = np.empty_like(by.value)
        else:
            x_out = np.empty_like(bx)
            y_out = np.empty_like(by)

        # We now loop over every unique value of y and z and compute the transform.
        # This means we make the minimum number of calls possible to the transform.
        for yyind in np.unique(yind):
            for zzind in np.unique(zind):
                # Scalar parameters are reshaped to be length one arrays by modeling
                sct = self.transform_at_index((zzind, yyind), crpix[0], cdelt[0], lon_pole[0])

                # Call this transform for all values of x, y where z == zind
                mask = np.logical_and(zind == zzind, yind == yyind)
                if inverse:
                    # Note this isn't use as the inverse of this model uses the
                    # standard 2D inverse.
                    xx, yy = sct.inverse(bx[mask], by[mask])  # pragma: no cover
                else:
                    xx, yy = sct(bx[mask], by[mask])

                if isinstance(xx, u.Quantity):
                    x_out[mask], y_out[mask] = xx.value, yy.value
                else:
                    x_out[mask], y_out[mask] = xx, yy

        # Put the units back
        if isinstance(xx, u.Quantity):
            x_out = x_out << xx.unit
            y_out = y_out << yy.unit

        return x_out, y_out


class InverseVaryingCelestialTransformSlit2D(BaseVaryingCelestialTransform2D):
    n_inputs = 4
    n_outputs = 1

    @property
    def input_units(self):
        return {"lon": u.deg, "lat": u.deg, "raster": u.pix, "repeat": u.pix}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inputs = ("lon", "lat", "raster", "repeat")
        self.outputs = ("slit-y",)

    def evaluate(self, lon, lat, raster, repeat, crpix, cdelt, lon_pole, **kwargs):
        return self._map_transform(lon, lat, raster, repeat, crpix, cdelt,
                                   lon_pole, inverse=True)[0]


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

        total_inputs = self.n_outputs
        n_left_only_inputs = total_inputs - self.shared_inputs

        # Pass through arguments to the left model unchanged while computing the right output
        mapping = list(range(n_left_only_inputs))
        step1 = m.Mapping(mapping) & right_inverse

        # Now pass through the right outputs unchanged while also feeding them into the left model

        # This mapping duplicates the output of the right inverse to be fed
        # into the left and also out unmodified at the end of the transform
        inter_mapping = mapping + list(range(max(mapping) + 1, max(mapping) + 1 + right_inverse.n_outputs)) * 2
        step2 = m.Mapping(inter_mapping) | (left_inverse & m.Identity(right_inverse.n_outputs))

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


def varying_celestial_transform_from_tables(crpix: Union[Iterable[float], u.Quantity],
                                            cdelt: Union[Iterable[float], u.Quantity],
                                            pc_table: Union[ArrayLike, u.Quantity],
                                            crval_table: Union[Iterable[float], u.Quantity],
                                            lon_pole: Union[float, u.Quantity] = None,
                                            projection: Model = m.Pix2Sky_TAN(),
                                            inverse=False,
                                            slit=False,
                                            ) -> BaseVaryingCelestialTransform:
    """
    Generate a `.BaseVaryingCelestialTransform` based on the dimensionality of the tables.
    """

    table_shape, _, _ = BaseVaryingCelestialTransform._validate_table_shapes(pc_table,
                                                                             crval_table)

    if (table_d := len(table_shape)) not in (1, 2):
        raise ValueError("Only one or two dimensional lookup tables are supported.")

    if inverse:
        cls = InverseVaryingCelestialTransform
        if slit:
            cls = InverseVaryingCelestialTransformSlit
        if table_d == 2:
            cls = InverseVaryingCelestialTransform2D
            if slit:
                cls = InverseVaryingCelestialTransformSlit2D
    else:
        cls = VaryingCelestialTransform
        if slit:
            cls = VaryingCelestialTransformSlit
        if table_d == 2:
            cls = VaryingCelestialTransform2D
            if slit:
                cls = VaryingCelestialTransformSlit2D

    return cls(
        crpix=crpix,
        cdelt=cdelt,
        crval_table=crval_table,
        pc_table=pc_table,
        lon_pole=lon_pole,
        projection=projection
    )
