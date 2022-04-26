import numpy as np
import pytest

import astropy.modeling.models as m
import astropy.units as u
from astropy.coordinates.matrix_utilities import rotation_matrix
from astropy.modeling import CompoundModel

from dkist.wcs.models import (VaryingCelestialTransform, VaryingCelestialTransform2D,
                              VaryingCelestialTransformSlit, VaryingCelestialTransformSlit2D,
                              generate_celestial_transform,
                              varying_celestial_transform_from_tables)


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

    trans5 = vct.transform_at_index(5)
    assert isinstance(trans5, CompoundModel)

    # Verify that we have the 5th matrix in the series
    affine = trans5.left.left.right
    assert isinstance(affine, m.AffineTransformation2D)
    assert u.allclose(affine.matrix, varying_matrix_lt[5])
    # x.shape=(1,), y.shape=(1,), z.shape=(1,)
    pixel = (0*u.pix, 0*u.pix, 5*u.pix)
    world = vct(*pixel)
    assert np.array(world[0]).shape == ()
    assert u.allclose(world, (359.99804329*u.deg, 0.00017119*u.deg))
    assert u.allclose(vct.inverse(*world, 5*u.pix), pixel[:2], atol=0.01*u.pix)


@pytest.mark.parametrize(("pixel", "lon_shape"), (
    ((*np.mgrid[0:10, 0:10] * u.pix, np.arange(10) * u.pix), (10, 10)),
    (np.mgrid[0:10, 0:10, 0:5] * u.pix, (10, 10, 5)),
    ((2 * u.pix, 2 * u.pix, np.arange(10) * u.pix), (10,)),
    ((np.arange(10) * u.pix,
      np.arange(10) * u.pix,
      np.arange(10)[..., None] * u.pix), (10, 10)),
    (np.mgrid[0:1024, 0:1000, 0:2] * u.pix, (1024, 1000, 2)),
))
def test_varying_transform_pc_shapes(pixel, lon_shape):
    varying_matrix_lt = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 10)] * u.arcsec

    vct = VaryingCelestialTransform(crpix=(5, 5) * u.pix,
                                    cdelt=(1, 1) * u.arcsec/u.pix,
                                    crval_table=(0, 0) * u.arcsec,
                                    pc_table=varying_matrix_lt,
                                    lon_pole=180 * u.deg)
    world = vct(*pixel)
    assert np.array(world[0]).shape == lon_shape
    new_pixel = vct.inverse(*world, pixel[-1])
    assert u.allclose(new_pixel,
                      np.broadcast_arrays(*pixel, subok=True)[:2],
                      atol=0.01*u.pix)


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

    trans2 = vct.transform_at_index(2)
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


def test_varying_transform_4d_pc():
    varying_matrix_lt = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 15)] * u.arcsec
    varying_matrix_lt = varying_matrix_lt.reshape((3, 5, 2, 2))

    vct = VaryingCelestialTransform2D(crpix=(5, 5) * u.pix,
                                      cdelt=(1, 1) * u.arcsec/u.pix,
                                      crval_table=(0, 0) * u.arcsec,
                                      pc_table=varying_matrix_lt,
                                      lon_pole=180 * u.deg)

    pixel = 0*u.pix, 0*u.pix, 0*u.pix, 0*u.pix
    world = vct(*pixel)
    new_pixel = vct.inverse(*world, 0*u.pix, 0*u.pix)

    assert u.allclose(new_pixel, pixel[:2], atol=0.01*u.pix)

    out_of_bounds = u.Quantity(vct(*(0, 0, -10, 0) * u.pix))
    assert isinstance(out_of_bounds, u.Quantity)
    assert out_of_bounds.unit.is_equivalent(u.deg)
    assert np.isnan(out_of_bounds.value).all()


def test_varying_transform_4d_pc_unitless():
    varying_matrix_lt = np.array([rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 15)])
    varying_matrix_lt = varying_matrix_lt.reshape((3, 5, 2, 2))

    vct = VaryingCelestialTransform2D(crpix=(5, 5),
                                      cdelt=(1, 1),
                                      crval_table=(0, 0),
                                      pc_table=varying_matrix_lt,
                                      lon_pole=180)

    pixel = 0, 0, 0, 0
    world = vct(*pixel)
    new_pixel = vct.inverse(*world, 0, 0)

    assert u.allclose(new_pixel, pixel[:2], atol=0.01)
    assert np.isnan(vct(0, 0, -10, 0)).all()


@pytest.mark.parametrize(("pixel", "lon_shape"), (
    ((*np.mgrid[0:5, 0:5] * u.pix, np.arange(5) * u.pix, 0 * u.pix), (5, 5)),
    (np.mgrid[0:10, 0:10, 0:5, 0:3] * u.pix, (10, 10, 5, 3)),
    ((2 * u.pix, 2 * u.pix, 0*u.pix, np.arange(3) * u.pix), (3,)),
    ((np.arange(10) * u.pix,
      np.arange(10) * u.pix,
      np.arange(5)[..., None] * u.pix,
      np.arange(3)[..., None, None]), (3, 5, 10)),
))
def test_varying_transform_4d_pc_shapes(pixel, lon_shape):
    varying_matrix_lt = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 15)] * u.arcsec
    varying_matrix_lt = varying_matrix_lt.reshape((5, 3, 2, 2))

    vct = VaryingCelestialTransform2D(crpix=(5, 5) * u.pix,
                                      cdelt=(1, 1) * u.arcsec/u.pix,
                                      crval_table=(0, 0) * u.arcsec,
                                      pc_table=varying_matrix_lt,
                                      lon_pole=180 * u.deg)
    world = vct(*pixel)
    assert np.array(world[0]).shape == lon_shape
    new_pixel = vct.inverse(*world, *pixel[-2:])
    assert u.allclose(new_pixel,
                      np.broadcast_arrays(*pixel, subok=True)[:2],
                      atol=0.01*u.pix)


def test_vct_dispatch():
    varying_matrix_lt = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 15)] * u.arcsec
    varying_matrix_lt = varying_matrix_lt.reshape((5, 3, 2, 2))

    crval_table = list(zip(np.arange(1, 16), np.arange(16, 31))) * u.arcsec
    crval_table = crval_table.reshape((5, 3, 2))

    kwargs = dict(crpix=(5, 5) * u.pix,
                  cdelt=(1, 1) * u.arcsec/u.pix,
                  lon_pole=180 * u.deg)

    vct_3d = varying_celestial_transform_from_tables(pc_table=varying_matrix_lt[0],
                                                     crval_table=crval_table[0],
                                                     **kwargs)

    assert isinstance(vct_3d, VaryingCelestialTransform)

    vct_2d = varying_celestial_transform_from_tables(pc_table=varying_matrix_lt,
                                                     crval_table=crval_table,
                                                     **kwargs)

    assert isinstance(vct_2d, VaryingCelestialTransform2D)

    with pytest.raises(ValueError, match="Only one or two dimensional lookup tables are supported"):
        varying_celestial_transform_from_tables(pc_table=varying_matrix_lt[1:].reshape((3, 2, 2, 2, 2)),
                                                crval_table=crval_table[1:].reshape((3, 2, 2, 2)),
                                                **kwargs)


def test_vct_shape_errors():
    pc_table = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 15)] * u.arcsec
    pc_table = pc_table.reshape((5, 3, 2, 2))

    crval_table = list(zip(np.arange(1, 16), np.arange(16, 31))) * u.arcsec
    crval_table = crval_table.reshape((5, 3, 2))

    kwargs = dict(crpix=(5, 5) * u.pix,
                  cdelt=(1, 1) * u.arcsec/u.pix,
                  lon_pole=180 * u.deg)

    with pytest.raises(ValueError, match="only be constructed with a one dimensional"):
        VaryingCelestialTransform(crval_table=crval_table, pc_table=pc_table, **kwargs)

    with pytest.raises(ValueError, match="only be constructed with a one dimensional"):
        VaryingCelestialTransformSlit(crval_table=crval_table, pc_table=pc_table, **kwargs)

    with pytest.raises(ValueError, match="only be constructed with a two dimensional"):
        VaryingCelestialTransform2D(crval_table=crval_table[0], pc_table=pc_table[0], **kwargs)

    with pytest.raises(ValueError, match="only be constructed with a two dimensional"):
        VaryingCelestialTransformSlit2D(crval_table=crval_table[0], pc_table=pc_table[0], **kwargs)


def test_vct_slit():
    pc_table = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 10)] * u.arcsec

    kwargs = dict(crpix=(5, 5) * u.pix,
                  cdelt=(1, 1) * u.arcsec/u.pix,
                  crval_table=(0, 0) * u.arcsec,
                  lon_pole=180 * u.deg)

    vct_slit = VaryingCelestialTransformSlit(pc_table=pc_table, **kwargs)
    pixel = (0*u.pix, 0*u.pix)
    world = vct_slit(*pixel)
    ipixel = vct_slit.inverse(*world, 0*u.pix)
    assert u.allclose(ipixel, pixel[0], atol=1e-5*u.pix)

    world2 = vct_slit(pixel[0], 1*u.pix)
    assert not u.allclose(world, world2)


def test_vct_slit2d():
    pc_table = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 15)] * u.arcsec
    pc_table = pc_table.reshape((5, 3, 2, 2))

    kwargs = dict(crpix=(5, 5) * u.pix,
                  cdelt=(1, 1) * u.arcsec/u.pix,
                  crval_table=(0, 0) * u.arcsec,
                  lon_pole=180 * u.deg)

    vct_slit = VaryingCelestialTransformSlit2D(pc_table=pc_table, **kwargs)
    pixel = (0*u.pix, 0*u.pix, 0*u.pix)
    world = vct_slit(*pixel)
    ipixel = vct_slit.inverse(*world, 0*u.pix, 0*u.pix)
    assert u.allclose(ipixel, pixel[0], atol=1e-5*u.pix)


def test_vct_slit_unitless():
    pc_table = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 10)]

    kwargs = dict(crpix=(5, 5),
                  cdelt=(1, 1),
                  crval_table=(0, 0),
                  lon_pole=180)

    vct_slit = VaryingCelestialTransformSlit(pc_table=pc_table, **kwargs)
    pixel = (0, 0)
    world = vct_slit(*pixel)
    ipixel = vct_slit.inverse(*world, 0)
    assert u.allclose(ipixel, pixel[0], atol=1e-5)

    world2 = vct_slit(pixel[0], 1)
    assert not u.allclose(world, world2)


def test_vct_slit2d_unitless():
    pc_table = np.array([rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 15)])
    pc_table = pc_table.reshape((5, 3, 2, 2))

    kwargs = dict(crpix=(5, 5),
                  cdelt=(1, 1),
                  crval_table=(0, 0),
                  lon_pole=180)

    vct_slit = VaryingCelestialTransformSlit2D(pc_table=pc_table, **kwargs)
    pixel = (0, 0, 0)
    world = vct_slit(*pixel)
    ipixel = vct_slit.inverse(*world, 0, 0)
    assert u.allclose(ipixel, pixel[0], atol=1e-5)
