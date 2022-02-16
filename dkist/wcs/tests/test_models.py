import numpy as np
import pytest

import astropy.modeling.models as m
import astropy.units as u
from astropy.coordinates.matrix_utilities import rotation_matrix
from astropy.modeling import CompoundModel

from dkist.wcs.models import (CoupledCompoundModel, VaryingCelestialTransform,
                              generate_celestial_transform)


def test_generate_celestial():
    tfrm = generate_celestial_transform(
        crpix=[0, 0] * u.pix,
        crval=[0, 0] * u.arcsec,
        cdelt=[1, 1] * u.arcsec/u.pix,
        pc=np.identity(2) * u.arcsec,
    )

    # Traverse the tree to make sure it's what we expect
    assert isinstance(tfrm, CompoundModel)
    assert isinstance(tfrm.right, m.RotateNative2Celestial)
    assert isinstance(tfrm.left.right, m.Pix2Sky_TAN)
    assert isinstance(tfrm.left.left.right, m.AffineTransformation2D)
    assert isinstance(tfrm.left.left.left.right, CompoundModel)
    assert isinstance(tfrm.left.left.left.right.left, m.Multiply)
    assert isinstance(tfrm.left.left.left.left, CompoundModel)
    assert isinstance(tfrm.left.left.left.left.right, m.Shift)

    # Copout and only test that one parameter has units
    shift1 = tfrm.left.left.left.left.right
    assert u.allclose(shift1.offset, 0 * u.pix)


def test_generate_celestial_unitless():
    tfrm = generate_celestial_transform(
        crpix=[0, 0],
        crval=[0, 0],
        cdelt=[1, 1],
        pc=np.identity(2),
    )
    shift1 = tfrm.left.left.left.left.right
    assert u.allclose(shift1.offset, 0)


def test_varying_transform_pc():
    varying_matrix_lt = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 10)] * u.arcsec

    vct = VaryingCelestialTransform(crpix=(5, 5) * u.pix,
                                    cdelt=(1, 1) * u.arcsec/u.pix,
                                    crval_table=(0, 0) * u.arcsec,
                                    pc_table=varying_matrix_lt,
                                    lon_pole=180 * u.deg)

    trans5 = vct.transform_at_index(5*u.pix)
    assert isinstance(trans5, CompoundModel)

    # Verify that we have the 5th matrix in the series
    affine = trans5.left.left.right
    assert isinstance(affine, m.AffineTransformation2D)
    assert u.allclose(affine.matrix, varying_matrix_lt[5])

    pixel = (0*u.pix, 0*u.pix, 5*u.pix)
    world = vct(*pixel)
    assert u.allclose(world, (359.99804329*u.deg, 0.00017119*u.deg))

    assert u.allclose(vct.inverse(*world, 5*u.pix), pixel[:2], atol=0.01*u.pix)


def test_varying_transform_pc_unitless():
    varying_matrix_lt = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 10)]

    vct = VaryingCelestialTransform(crpix=(5, 5),
                                    # without units everything is deg, so make this arcsec in deg
                                    cdelt=((1, 1)*u.arcsec).to_value(u.deg),
                                    crval_table=(0, 0),
                                    pc_table=varying_matrix_lt,
                                    lon_pole=180)

    trans5 = vct.transform_at_index(5)
    assert isinstance(trans5, CompoundModel)

    # Verify that we have the 5th matrix in the series
    affine = trans5.left.left.right
    assert isinstance(affine, m.AffineTransformation2D)
    assert u.allclose(affine.matrix, varying_matrix_lt[5])

    pixel = (0, 0, 5)
    world = vct(*pixel)
    assert np.allclose(world, (359.99804329, 0.00017119))

    assert np.allclose(vct.inverse(*world, 5), pixel[:2], atol=0.01)


def test_varying_transform_crval():
    crval_table = ((0, 1), (2, 3), (4, 5)) * u.arcsec
    vct = VaryingCelestialTransform(crpix=(5, 5) * u.pix,
                                    cdelt=(1, 1) * u.arcsec/u.pix,
                                    crval_table=crval_table,
                                    pc_table=np.identity(2) * u.arcsec,
                                    lon_pole=180 * u.deg)

    trans2 = vct.transform_at_index(2*u.pix)
    assert isinstance(trans2, CompoundModel)

    # Verify that we have the 2nd crval pair in the series
    crval1 = trans2.right.lon
    crval2 = trans2.right.lat
    assert u.allclose(crval1, crval_table[2][0])
    assert u.allclose(crval2, crval_table[2][1])

    pixel = (0*u.pix, 0*u.pix, 2*u.pix)
    world = vct(*pixel)
    assert u.allclose(world, (3.59999722e+02, 2.78325906e-13)*u.deg)

    assert u.allclose(vct.inverse(*world, 2*u.pix), pixel[:2], atol=0.01*u.pix)


def test_vct_errors():
    with pytest.raises(ValueError, match="pc table should be"):
        VaryingCelestialTransform(crpix=(5, 5),
                                  cdelt=(1, 1),
                                  crval_table=(0, 0),
                                  pc_table=[[1, 2, 3],
                                            [4, 4, 6],
                                            [7, 8, 9]],
                                  lon_pole=180)

    with pytest.raises(ValueError, match="crval table should be"):
        VaryingCelestialTransform(crpix=(5, 5),
                                  cdelt=(1, 1),
                                  crval_table=((0, 0, 0),),
                                  pc_table=[[1, 2],
                                            [4, 4]],
                                  lon_pole=180)

    with pytest.raises(ValueError,
                       match="The shape of the pc and crval tables should match"):
        VaryingCelestialTransform(crpix=(5, 5),
                                  cdelt=(1, 1),
                                  crval_table=((0, 0), (1, 1), (2, 2)),
                                  pc_table=[[[1, 2],
                                             [4, 4]],
                                            [[1, 2],
                                             [3, 4]]],
                                  lon_pole=180)

    with pytest.raises(TypeError,
                       match="projection keyword should"):
        VaryingCelestialTransform(crpix=(5, 5),
                                  cdelt=(1, 1),
                                  crval_table=((0, 0), (1, 1)),
                                  pc_table=[[[1, 2],
                                             [4, 4]],
                                            [[1, 2],
                                             [3, 4]]],
                                  lon_pole=180,
                                  projection=ValueError)


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
