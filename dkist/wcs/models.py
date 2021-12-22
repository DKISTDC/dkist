import numpy as np

import astropy.modeling.models as m
import astropy.units as u
from astropy.modeling import CompoundModel, Model, Parameter

__all__ = ['CoupledCompoundModel',
           'InverseVaryingCelestialTransform',
           'VaryingCelestialTransform',
           'BaseVaryingCelestialTransform',
           'SimpleCelestialTransform']


# TODO: (soon) Decide if we want to keep this model around at all.
# Pros: Easier to reason with, easier for users to modify
# Cons: non-standard, need to serialise it, no hard requirement on it, just
# need a function to generate the compound model for the given input
class SimpleCelestialTransform(Model):
    """
    A representation of a celestial WCS as described in the FITS specification.
    """

    n_inputs = 2
    n_outputs = 2

    crpix = Parameter()
    cdelt = Parameter()
    pc = Parameter(default=[[1.0, 0.0], [0.0, 1.0]])
    crval = Parameter()
    lon_pole = Parameter(default=180)

    standard_broadcasting = False
    _separable = False
    _input_units_allow_dimensionless = True

    @property
    def input_units(self):
        return {"x": u.pix, "y": u.pix}

    def __init__(self, *args, projection=m.Pix2Sky_TAN(), **kwargs):
        super().__init__(*args, **kwargs)
        if type(self) is SimpleCelestialTransform:
            self.inputs = ("x", "y")
        self.outputs = ("lon", "lat")
        if not isinstance(projection, m.Pix2SkyProjection):
            raise TypeError("The projection keyword should be a Pix2SkyProjection model class.")
        self.projection = projection

    # TODO: Evaluate if this method should be replaced with
    # https://github.com/spacetelescope/gwcs/blob/master/gwcs/utils.py#L328
    def _generate_transform(self,
                            crpix,
                            cdelt,
                            pc,
                            crval,
                            lon_pole):

        # Make translation unitful if all parameters have units
        translation = (0, 0)
        if hasattr(pc, "unit") and pc.unit is not None:
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
        return shift | scale | rot | self.projection | skyrot

    def evaluate(self,
                 x,
                 y,
                 crpix,
                 cdelt,
                 pc,
                 crval,
                 lon_pole):

        celestial = self._generate_transform(crpix[0],
                                             cdelt[0],
                                             pc[0],
                                             crval[0],
                                             lon_pole)
        return celestial(x, y)

    @property
    def inverse(self):
        celestial = self._generate_transform(self.crpix,
                                             self.cdelt,
                                             self.pc,
                                             self.crval,
                                             self.lon_pole)
        return celestial.inverse


class BaseVaryingCelestialTransform(Model):
    """
    Shared components between the forward and reverse varying celestial transforms.
    """

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

        return table_shape

    @staticmethod
    def get_pc_crval(z, pc, crval):
        # Get crval and pc
        if isinstance(z, u.Quantity):
            ind = int(z.value)
        else:
            ind = int(z)
        if pc.shape != (2, 2):
            pc = pc[ind]
        if crval.shape != (2,):
            crval = crval[ind]
        return pc, crval

    def __init__(self, *args, crval_table=None, pc_table=None, projection=m.Pix2Sky_TAN(), **kwargs):
        super().__init__(*args, **kwargs)

        self.pc_table = np.asanyarray(pc_table)
        self.crval_table = np.asanyarray(crval_table)
        self.table_shape = self._validate_table_shapes(self.pc_table, self.crval_table)

        if not isinstance(projection, m.Pix2SkyProjection):
            raise TypeError("The projection keyword should be a Pix2SkyProjection model class.")
        self.projection = projection



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

    @property
    def input_units(self):
        return {"x": u.pix, "y": u.pix, "z": u.pix}

    def transform_at_index(self, z):
        pc, crval = self.get_pc_crval(z, self.pc_table, self.crval_table)
        return SimpleCelestialTransform(crpix=self.crpix,
                                        cdelt=self.cdelt,
                                        pc=pc,
                                        crval=crval,
                                        lon_pole=self.lon_pole,
                                        projection=self.projection)

    def evaluate(self, x, y, z, crpix, cdelt, lon_pole):
        pc, crval = self.get_pc_crval(z, self.pc_table, self.crval_table)

        sct = SimpleCelestialTransform(crpix=crpix[0],
                                       cdelt=cdelt[0],
                                       pc=pc,
                                       crval=crval,
                                       lon_pole=lon_pole[0],
                                       projection=self.projection)
        return sct(x, y)

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
        pc, crval = self.get_pc_crval(z,
                                      self.pc_table,
                                      self.crval_table)

        sct = SimpleCelestialTransform(crpix=crpix[0],
                                       cdelt=cdelt[0],
                                       pc=pc,
                                       crval=crval,
                                       lon_pole=lon_pole[0],
                                       projection=self.projection)

        return sct.inverse(lon, lat)


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
    forward direction:

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
    which duplicates the output of the right hand side model.

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
        self.inputs = self.inputs[:-shared_inputs]
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
        step2 = m.Mapping(inter_mapping) | (left_inverse & m.Mapping(list(range(right_inverse.n_outputs))))

        return step1 | step2
