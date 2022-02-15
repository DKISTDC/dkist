import numpy as np

import astropy.modeling.models as m
import astropy.units as u
from asdf.testing.helpers import roundtrip_object
from astropy.coordinates.matrix_utilities import rotation_matrix
from astropy.modeling import CompoundModel

from dkist.wcs.models import (CoupledCompoundModel, InverseVaryingCelestialTransform,
                              VaryingCelestialTransform)


def test_roundtrip_vct():
    varying_matrix_lt = [rotation_matrix(a)[:2, :2]
                         for a in np.linspace(0, 90, 10)] * u.arcsec

    vct = VaryingCelestialTransform(crpix=(5, 5) * u.pix,
                                    cdelt=(1, 1) * u.arcsec/u.pix,
                                    crval_table=(0, 0) * u.arcsec,
                                    pc_table=varying_matrix_lt,
                                    lon_pole=180 * u.deg)
    new_vct = roundtrip_object(vct)
    assert isinstance(new_vct, VaryingCelestialTransform)
    new_ivct = roundtrip_object(vct.inverse)
    assert isinstance(new_ivct, InverseVaryingCelestialTransform)

    assert u.allclose(u.Quantity(new_vct.crpix), (5, 5) * u.pix)
    assert u.allclose(u.Quantity(new_ivct.crpix), (5, 5) * u.pix)

    assert u.allclose(u.Quantity(new_vct.pc_table), varying_matrix_lt)
    assert u.allclose(u.Quantity(new_ivct.pc_table), varying_matrix_lt)

    pixel = (0*u.pix, 0*u.pix, 5*u.pix)
    world = new_vct(*pixel)
    assert u.allclose(world, (359.99804329*u.deg, 0.00017119*u.deg))

    assert u.allclose(new_ivct(*world, 5*u.pix), pixel[:2], atol=0.01*u.pix)


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
