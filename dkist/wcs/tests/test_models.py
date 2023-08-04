import numpy as np
import pytest
from numpy.random import default_rng

import astropy.modeling.models as m
import astropy.units as u
from astropy.coordinates.matrix_utilities import rotation_matrix
from astropy.modeling import CompoundModel
from astropy.modeling.models import Tabular1D

from dkist.wcs.models import (Ravel, Unravel, VaryingCelestialTransform,
                              VaryingCelestialTransform2D, VaryingCelestialTransform3D,
                              VaryingCelestialTransformSlit, VaryingCelestialTransformSlit2D,
                              VaryingCelestialTransformSlit3D, generate_celestial_transform,
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


def test_varying_transform_no_lon_pole_unit():
    varying_matrix_lt = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 10)] * u.arcsec
    # Without a lon_pole passed, the transform was originally setting
    # the unit for it to be the same as crval, which is wrong.
    vct = VaryingCelestialTransform(
        crpix=(5, 5) * u.pix,
        cdelt=(1, 1) * u.arcsec/u.pix,
        crval_table=(0, 0) * u.arcsec,
        pc_table=varying_matrix_lt,
    )
    trans5 = vct.transform_at_index(5)
    assert isinstance(trans5, CompoundModel)
    assert u.allclose(trans5.right.lon_pole, 180 * u.deg)

def test_varying_transform_pc():
    varying_matrix_lt = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 10)] * u.arcsec

    vct = VaryingCelestialTransform(
        crpix=(5, 5) * u.pix,
        cdelt=(1, 1) * u.arcsec/u.pix,
        crval_table=(0, 0) * u.arcsec,
        pc_table=varying_matrix_lt,
        lon_pole=180 * u.deg,
    )

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

    vct = VaryingCelestialTransform(
        crpix=(5, 5) * u.pix,
        cdelt=(1, 1) * u.arcsec/u.pix,
        crval_table=(0, 0) * u.arcsec,
        pc_table=varying_matrix_lt,
        lon_pole=180 * u.deg,
    )
    world = vct(*pixel)
    assert np.array(world[0]).shape == lon_shape
    new_pixel = vct.inverse(*world, pixel[-1])
    assert u.allclose(new_pixel,
                      np.broadcast_arrays(*pixel, subok=True)[:2],
                      atol=0.01*u.pix)


def test_varying_transform_pc_unitless():
    varying_matrix_lt = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 10)]

    vct = VaryingCelestialTransform(
        crpix=(5, 5),
        # without units everything is deg, so make this arcsec in deg
        cdelt=((1, 1)*u.arcsec).to_value(u.deg),
        crval_table=(0, 0),
        pc_table=varying_matrix_lt,
        lon_pole=180,
    )

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
    vct = VaryingCelestialTransform(
        crpix=(5, 5) * u.pix,
        cdelt=(1, 1) * u.arcsec/u.pix,
        crval_table=crval_table,
        pc_table=np.identity(2) * u.arcsec,
        lon_pole=180 * u.deg,
    )

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
        VaryingCelestialTransform(
            crpix=(5, 5),
            cdelt=(1, 1),
            crval_table=(0, 0),
            pc_table=[[1, 2, 3],
                      [4, 4, 6],
                      [7, 8, 9]],
            lon_pole=180,
        )

    with pytest.raises(ValueError, match="crval table should be"):
        VaryingCelestialTransform(
            crpix=(5, 5),
            cdelt=(1, 1),
            crval_table=((0, 0, 0),),
            pc_table=[[1, 2],
                      [4, 4]],
            lon_pole=180,
        )

    with pytest.raises(ValueError,
                       match="The shape of the pc and crval tables should match"):
        VaryingCelestialTransform(
            crpix=(5, 5),
            cdelt=(1, 1),
            crval_table=((0, 0), (1, 1), (2, 2)),
            pc_table=[[[1, 2],
                       [4, 4]],
                      [[1, 2],
                       [3, 4]]],
            lon_pole=180,
        )

    with pytest.raises(TypeError,
                       match="projection keyword should"):
        VaryingCelestialTransform(
            crpix=(5, 5),
            cdelt=(1, 1),
            crval_table=((0, 0), (1, 1)),
            pc_table=[[[1, 2],
                       [4, 4]],
                      [[1, 2],
                       [3, 4]]],
            lon_pole=180,
            projection=ValueError,
        )


def test_varying_transform_4d_pc():
    varying_matrix_lt = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 15)] * u.arcsec
    varying_matrix_lt = varying_matrix_lt.reshape((3, 5, 2, 2))

    vct = VaryingCelestialTransform2D(
        crpix=(5, 5) * u.pix,
        cdelt=(1, 1) * u.arcsec/u.pix,
        crval_table=(0, 0) * u.arcsec,
        pc_table=varying_matrix_lt,
        lon_pole=180 * u.deg,
    )

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

    vct = VaryingCelestialTransform2D(
        crpix=(5, 5),
        cdelt=(1, 1),
        crval_table=(0, 0),
        pc_table=varying_matrix_lt,
        lon_pole=180,
    )

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

    vct = VaryingCelestialTransform2D(
        crpix=(5, 5) * u.pix,
        cdelt=(1, 1) * u.arcsec/u.pix,
        crval_table=(0, 0) * u.arcsec,
        pc_table=varying_matrix_lt,
        lon_pole=180 * u.deg,
    )
    world = vct(*pixel)
    assert np.array(world[0]).shape == lon_shape
    new_pixel = vct.inverse(*world, *pixel[-2:])
    assert u.allclose(new_pixel,
                      np.broadcast_arrays(*pixel, subok=True)[:2],
                      atol=0.01*u.pix)


def test_vct_dispatch():
    varying_matrix_lt = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 16)] * u.arcsec
    varying_matrix_lt = varying_matrix_lt.reshape((2, 2, 2, 2, 2, 2))
    crval_table = list(zip(np.arange(1, 17), np.arange(17, 33))) * u.arcsec
    crval_table = crval_table.reshape((2, 2, 2, 2, 2))
    kwargs = dict(
        crpix=(5, 5) * u.pix,
        cdelt=(1, 1) * u.arcsec/u.pix,
        lon_pole=180 * u.deg,
    )

    vct = varying_celestial_transform_from_tables(
        pc_table=varying_matrix_lt[0, 0, 0],
        crval_table=crval_table[0, 0, 0],
        **kwargs,
    )
    assert isinstance(vct, VaryingCelestialTransform)

    vct_2d = varying_celestial_transform_from_tables(
        pc_table=varying_matrix_lt[0, 0],
        crval_table=crval_table[0, 0],
        **kwargs,
    )
    assert isinstance(vct_2d, VaryingCelestialTransform2D)

    vct_3d = varying_celestial_transform_from_tables(
        pc_table=varying_matrix_lt[0],
        crval_table=crval_table[0],
        **kwargs
    )
    assert isinstance(vct_3d, VaryingCelestialTransform3D)

    with pytest.raises(ValueError, match="Only 1D, 2D and 3D lookup tables are supported."):
        varying_celestial_transform_from_tables(
            pc_table=varying_matrix_lt,
            crval_table=crval_table,
            **kwargs,
        )


def test_vct_shape_errors():
    pc_table = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, 15)] * u.arcsec
    pc_table = pc_table.reshape((5, 3, 2, 2))

    crval_table = list(zip(np.arange(1, 16), np.arange(16, 31))) * u.arcsec
    crval_table = crval_table.reshape((5, 3, 2))

    kwargs = dict(
        crpix=(5, 5) * u.pix,
        cdelt=(1, 1) * u.arcsec/u.pix,
        lon_pole=180 * u.deg,
    )

    with pytest.raises(ValueError, match="only be constructed with a one dimensional"):
        VaryingCelestialTransform(crval_table=crval_table, pc_table=pc_table, **kwargs)

    with pytest.raises(ValueError, match="only be constructed with a one dimensional"):
        VaryingCelestialTransformSlit(crval_table=crval_table, pc_table=pc_table, **kwargs)

    with pytest.raises(ValueError, match="only be constructed with a two dimensional"):
        VaryingCelestialTransform2D(crval_table=crval_table[0], pc_table=pc_table[0], **kwargs)

    with pytest.raises(ValueError, match="only be constructed with a two dimensional"):
        VaryingCelestialTransformSlit2D(crval_table=crval_table[0], pc_table=pc_table[0], **kwargs)

@pytest.mark.parametrize("has_units", [pytest.param(True, id="With Units"), pytest.param(False, id="Without Units")])
def test_vct(has_units):
    # LUT is 1D, corresponding to the number of raster steps
    num_raster_steps = 10
    num_x_pts = 4
    num_y_pts = 8
    pc_table = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, num_raster_steps)]
    crpix = (3, 3)
    cdelt = (1, 1)
    crval_table = (0, 0)
    lon_pole = 180
    raster = np.arange(num_raster_steps)
    x = np.arange(num_x_pts)
    y = np.arange(num_y_pts)
    # a raster vector that is outside the table
    raster_1 = raster + 1
    atol = 1.e-5
    if has_units:
        pc_table *= u.arcsec
        crpix *= u.pix
        cdelt *= u.arcsec/u.pix
        crval_table *= u.arcsec
        lon_pole *= u.deg
        raster *= u.pix
        raster_1 *= u.pix
        atol *= u.pix
        x *= u.pix
        y *= u.pix
    kwargs = dict(
        crpix=crpix,
        cdelt=cdelt,
        crval_table=crval_table,
        lon_pole=lon_pole,
    )
    grid = np.meshgrid(x, y, raster, indexing='ij')
    grid2 = np.meshgrid(x, y, raster_1, indexing='ij')

    vct = VaryingCelestialTransform(pc_table=pc_table, **kwargs)
    # forward transform returns lat and long vectors
    world = vct(*grid)
    assert len(world) == 2
    grid_shape = grid[0].shape
    assert np.all([world_item.shape == grid_shape for world_item in world])
    assert np.all([grid_item.shape == grid_shape for grid_item in grid])
    # there should be no nans in world:
    assert not np.any(np.isnan(world))
    # reverse transform to get round trip
    ipixel = vct.inverse(*world, grid[2])
    # round trip should be the same as what we started with
    # grid[0:2] is the full set of (x, y) coordinates
    assert u.allclose(ipixel, grid[0:2], atol=atol)

    # grid2 has coordinates outside the lut boundaries and should have nans
    world2 = vct(*grid2)
    assert np.any(np.isnan([item for item in world2]))

@pytest.mark.parametrize("has_units", [pytest.param(True, id="With Units"), pytest.param(False, id="Without Units")])
def test_vct2d(has_units):
    # LUT is 2D, corresponding to:
    # 2D combinations of (n_meas, n_raster, n_maps)
    # (1, m, n) or (m, n, 1), m > 1, n > 1
    # (m, 1, n) is not used because it means only a single raster step
    # (m, n, q) is 3D and uses the vct3d class
    # we cannot know apriori what m and n represent for this use case
    num_raster_steps = 10
    num_x_pts = 4
    num_y_pts = 8
    num_other_steps = 3
    table_length = num_raster_steps * num_other_steps
    pc_table = np.array([rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, table_length)])
    pc_table = pc_table.reshape((num_other_steps, num_raster_steps, 2, 2))
    crpix = (3, 3)
    cdelt = (1, 1)
    crval_table = (0, 0)
    lon_pole = 180
    raster = np.arange(num_raster_steps)
    x = np.arange(num_x_pts)
    y = np.arange(num_y_pts)
    other_steps = np.arange(num_other_steps)
    # a raster vector that is outside the table
    raster_1 = raster + 1
    atol = 1.e-5
    if has_units:
        pc_table *= u.arcsec
        crpix *= u.pix
        cdelt *= u.arcsec/u.pix
        crval_table *= u.arcsec
        lon_pole *= u.deg
        raster *= u.pix
        raster_1 *= u.pix
        atol *= u.pix
        x *= u.pix
        y *= u.pix
        other_steps *= u.pix
    kwargs = dict(
        crpix=crpix,
        cdelt=cdelt,
        crval_table=crval_table,
        lon_pole=lon_pole,
    )
    grid = np.meshgrid(x, y, other_steps, raster, indexing='ij')
    grid2 = np.meshgrid(x, y, other_steps, raster_1, indexing='ij')

    vct = VaryingCelestialTransform2D(pc_table=pc_table, **kwargs)
    # forward transform returns lat and long vectors
    world = vct(*grid)
    assert len(world) == 2
    grid_shape = grid[0].shape
    assert np.all([world_item.shape == grid_shape for world_item in world])
    assert np.all([grid_item.shape == grid_shape for grid_item in grid])
    # there should be no nans in world:
    assert not np.any(np.isnan(world))
    # reverse transform to get round trip
    ipixel = vct.inverse(*world, grid[2], grid[3])
    # round trip should be the same as what we started with
    # grid[0:2] is the full set of (x, y) coordinates
    assert u.allclose(ipixel, grid[0:2], atol=atol)

    # grid2 has coordinates outside the lut boundaries and should have nans
    world2 = vct(*grid2)
    assert np.any(np.isnan([item for item in world2]))


@pytest.mark.parametrize("has_units", [pytest.param(True, id="With Units"), pytest.param(False, id="Without Units")])
def test_vct3d(has_units):
    # LUT is 3D, corresponding to:
    # All combinations of (n_meas, n_raster, n_maps)
    # where n_meas, n_raster, n_maps are all > 1
    # This use case currently occurs in only for Cryo CI
    num_raster_steps = 10
    num_x_pts = 4
    num_y_pts = 8
    num_meas = 2
    num_maps = 3
    table_length = num_raster_steps * num_meas * num_maps
    pc_table = np.array([rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, table_length)])
    pc_table = pc_table.reshape((num_meas, num_maps, num_raster_steps, 2, 2))
    crpix = (3, 3)
    cdelt = (1, 1)
    crval_table = (0, 0)
    lon_pole = 180
    raster = np.arange(num_raster_steps)
    x = np.arange(num_x_pts)
    y = np.arange(num_y_pts)
    map_steps = np.arange(num_maps)
    meas = np.arange(num_meas)
    # a raster vector that is outside the table
    raster_1 = raster + 1
    atol = 1.e-5
    if has_units:
        pc_table *= u.arcsec
        crpix *= u.pix
        cdelt *= u.arcsec / u.pix
        crval_table *= u.arcsec
        lon_pole *= u.deg
        raster *= u.pix
        raster_1 *= u.pix
        atol *= u.pix
        x *= u.pix
        y *= u.pix
        map_steps *= u.pix
        meas *= u.pix
    kwargs = dict(
        crpix=crpix,
        cdelt=cdelt,
        crval_table=crval_table,
        lon_pole=lon_pole,
    )
    grid = np.meshgrid(x, y, meas, map_steps, raster, indexing='ij')
    grid2 = np.meshgrid(x, y, meas, map_steps, raster_1, indexing='ij')

    vct = VaryingCelestialTransform3D(pc_table=pc_table, **kwargs)
    # forward transform returns lat and long vectors
    world = vct(*grid)
    assert len(world) == 2
    grid_shape = grid[0].shape
    assert np.all([world_item.shape == grid_shape for world_item in world])
    assert np.all([grid_item.shape == grid_shape for grid_item in grid])
    # there should be no nans in world:
    assert not np.any(np.isnan(world))
    # reverse transform to get round trip
    ipixel = vct.inverse(*world, grid[2], grid[3], grid[4])
    # round trip should be the same as what we started with
    # grid[0:2] is the full set of (x, y) coordinates
    assert u.allclose(ipixel, grid[0:2], atol=atol)

    # grid2 has coordinates outside the lut boundaries and should have nans
    world2 = vct(*grid2)
    assert np.any(np.isnan([item for item in world2]))


@pytest.mark.parametrize("has_units", [pytest.param(True, id="With Units"), pytest.param(False, id="Without Units")])
def test_vct_slit(has_units):
    # LUT is 1D, corresponding to the number of raster steps
    num_raster_steps = 10
    num_slit_steps = 5
    pc_table = [rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, num_raster_steps)]
    crpix = (3, 3)
    cdelt = (1, 1)
    crval_table = (0, 0)
    lon_pole = 180
    # make sure along_slit and raster are different so result axis lengths are different
    along_slit = np.arange(num_slit_steps)
    raster = np.arange(num_raster_steps)
    # a raster vector that is outside the table
    raster_1 = raster + 1
    atol = 1.e-5
    if has_units:
        pc_table *= u.arcsec
        crpix *= u.pix
        cdelt *= u.arcsec/u.pix
        crval_table *= u.arcsec
        lon_pole *= u.deg
        along_slit *= u.pix
        raster *= u.pix
        raster_1 *= u.pix
        atol *= u.pix
    kwargs = dict(
        crpix=crpix,
        cdelt=cdelt,
        crval_table=crval_table,
        lon_pole=lon_pole,
    )
    grid = np.meshgrid(along_slit, raster, indexing='ij')
    grid2 = np.meshgrid(along_slit, raster_1, indexing='ij')

    vct_slit = VaryingCelestialTransformSlit(pc_table=pc_table, **kwargs)
    # forward transform returns a tuple of lat and long vectors
    world = vct_slit(*grid)
    assert len(world) == 2
    grid_shape = grid[0].shape
    assert np.all([world_item.shape == grid_shape for world_item in world])
    assert np.all([grid_item.shape == grid_shape for grid_item in grid])
    # there should be no nans in world:
    assert not np.any(np.isnan(world))
    # reverse transform to get round trip
    ipixel = vct_slit.inverse(*world, grid[1])
    # round trip should be the same as what we started with
    assert u.allclose(ipixel, grid[0], atol=atol)

    # grid2 has coordinates outside the lut boundaries and should have nans
    world2 = vct_slit(*grid2)
    assert np.any(np.isnan(world2))


@pytest.mark.parametrize("has_units", [pytest.param(True, id="With Units"), pytest.param(False, id="Without Units")])
def test_vct_slit2d(has_units):
    # LUT is 2D, corresponding to:
    # 2D combinations of (n_meas, n_raster, n_maps)
    # (1, m, n) or (m, n, 1), m > 1, n > 1
    # (m, 1, n) is not used because it means only a single raster step
    # (m, n, q) is 3D and uses the slit3d class
    # we cannot know apriori what m and n represent for this use case
    num_raster_steps = 10
    num_other_steps = 3
    num_slit_steps = 5
    table_length = num_raster_steps * num_other_steps
    pc_table = np.array([rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, table_length)])
    pc_table = pc_table.reshape((num_other_steps, num_raster_steps, 2, 2))
    crpix = (3, 3)
    cdelt = (1, 1)
    crval_table = (0, 0)
    lon_pole = 180
    along_slit = np.arange(num_slit_steps)
    raster = np.arange(num_raster_steps)
    other_steps = np.arange(num_other_steps)
    # a raster vector that is outside the table
    raster_1 = raster + 1
    atol = 1.e-5
    if has_units:
        pc_table *= u.arcsec
        crpix *= u.pix
        cdelt *= u.arcsec/u.pix
        crval_table *= u.arcsec
        lon_pole *= u.deg
        along_slit *= u.pix
        raster *= u.pix
        raster_1 *= u.pix
        atol *= u.pix
        other_steps *= u.pix
    kwargs = dict(
        crpix=crpix,
        cdelt=cdelt,
        crval_table=crval_table,
        lon_pole=lon_pole,
    )
    grid = np.meshgrid(along_slit, other_steps, raster, indexing='ij')
    grid2 = np.meshgrid(along_slit, other_steps, raster_1, indexing='ij')

    vct_slit_2d = VaryingCelestialTransformSlit2D(pc_table=pc_table, **kwargs)

    # forward transform returns lat and long vectors
    world = vct_slit_2d(*grid)
    assert len(world) == 2
    grid_shape = grid[0].shape
    assert np.all([world_item.shape == grid_shape for world_item in world])
    assert np.all([grid_item.shape == grid_shape for grid_item in grid])
    # there should be no nans in world:
    assert not np.any(np.isnan(world))
    # reverse transform to get round trip
    ipixel = vct_slit_2d.inverse(*world, grid[1], grid[2])
    assert u.allclose(ipixel, grid[0], atol=atol)

    # grid2 has coordinates outside the lut boundaries and should have nans
    world2 = vct_slit_2d(*grid2)
    assert np.any(np.isnan(world2))


@pytest.mark.parametrize("has_units", [pytest.param(True, id="With Units"), pytest.param(False, id="Without Units")])
def test_vct_slit3d(has_units):
    # LUT is 3D, corresponding to:
    # All combinations of (n_meas, n_raster, n_maps)
    # where n_meas, n_raster, n_maps are all > 1
    # This use case currently occurs in only for Cryo SP
    num_raster_steps = 10
    num_meas = 2
    num_maps = 3
    num_slit_steps = 5
    table_length = num_raster_steps * num_meas * num_maps
    pc_table = np.array([rotation_matrix(a)[:2, :2] for a in np.linspace(0, 90, table_length)])
    pc_table = pc_table.reshape((num_meas, num_maps, num_raster_steps, 2, 2))
    crpix = (3, 3)
    cdelt=(1, 1)
    crval_table=(0, 0)
    lon_pole=180
    along_slit = np.arange(num_slit_steps)
    raster = np.arange(num_raster_steps)
    map_steps = np.arange(num_maps)
    meas = np.arange(num_meas)
    # a raster vector that is outside the table
    raster_1 = raster + 1
    atol = 1.e-5
    if has_units:
        pc_table *= u.arcsec
        crpix *= u.pix
        cdelt *= u.arcsec/u.pix
        crval_table *= u.arcsec
        lon_pole *= u.deg
        along_slit *= u.pix
        raster *= u.pix
        raster_1 *= u.pix
        atol *= u.pix
        map_steps *= u.pix
        meas *= u.pix
    kwargs = dict(
        crpix=crpix,
        cdelt=cdelt,
        crval_table=crval_table,
        lon_pole=lon_pole,
    )
    grid = np.meshgrid(along_slit, meas, map_steps, raster, indexing='ij')
    grid2 = np.meshgrid(along_slit, meas, map_steps, raster_1, indexing='ij')

    vct_slit_3d = VaryingCelestialTransformSlit3D(pc_table=pc_table, **kwargs)

    # forward transform returns lat and long vectors
    world = vct_slit_3d(*grid)
    assert len(world) == 2
    grid_shape = grid[0].shape
    assert np.all([world_item.shape == grid_shape for world_item in world])
    assert np.all([grid_item.shape == grid_shape for grid_item in grid])
    # there should be no nans in world:
    assert not np.any(np.isnan(world))
    # reverse transform to get round trip
    ipixel = vct_slit_3d.inverse(*world, grid[1], grid[2], grid[3])
    assert u.allclose(ipixel, grid[0], atol=atol)

    # grid2 has coordinates outside the lut boundaries and should have nans
    world2 = vct_slit_3d(*grid2)
    assert np.any(np.isnan(world2))

def _evaluate_ravel(array_shape, inputs, order="C"):
    """Evaluate the ravel computation using brute force for comparison with numpy result."""
    # NB: This method does not work with units...
    array_bounds = (array_shape - 1)
    # This if test is to handle multidimensional inputs properly
    if len(inputs.shape) > 1:
        array_bounds = array_bounds[:, np.newaxis]
    rounded_inputs = np.clip(np.rint(inputs).astype(int), None, array_bounds)
    if order == "F":
        array_shape = array_shape[::-1]
        inputs = inputs[::-1]
        rounded_inputs = rounded_inputs[::-1]
    offsets = np.cumprod(array_shape[1:][::-1])[::-1]
    result = np.dot(offsets, rounded_inputs[:-1]) + inputs[-1]
    return result


def _evaluate_unravel(array_shape, index, order="C"):
    """Evaluate the reverse ravel computation using brute force for comparison with numpy result."""
    # NB: This method does not work with units...
    if order == "F":
        array_shape = array_shape[::-1]
    offsets = np.cumprod(array_shape[1:][::-1])[::-1]
    curr_offset = index
    # This if test is to handle multidimensional inputs properly
    if isinstance(index, np.ndarray):
        output_shape = tuple([len(array_shape), len(index)])
    else:
        output_shape = len(array_shape)
    indices = np.zeros(output_shape, dtype=float)
    for i, offset in enumerate(offsets):
        indices[i] = np.floor_divide(curr_offset, offset)
        curr_offset = np.remainder(curr_offset, offset)
    indices[-1] = curr_offset
    if order == "F":
        indices = indices[::-1]
    return tuple(indices)

@pytest.mark.parametrize("ndim", [pytest.param(2, id='2D'), pytest.param(3, id='3D')])
@pytest.mark.parametrize("has_units", [pytest.param(True, id="With Units"), pytest.param(False, id="Without Units")])
@pytest.mark.parametrize("input_type", [pytest.param("array", id="Array Inputs"), pytest.param("scalar", id="Scalar Inputs")])
def test_ravel_model(ndim, has_units, input_type):
    rng = default_rng()
    array_shape = rng.integers(1, 21, ndim)
    array_bounds = array_shape - 1
    order = "C"
    ravel = Ravel(array_shape, order=order)
    units = u.pix
    if input_type == "array":
        # adding the new axis onto array_bounds makes broadcasting work below
        array_bounds = array_bounds[:, np.newaxis]
        # use 5 as an arbitrary number of inputs
        random_number_shape = len(array_shape), 5
    else:
        random_number_shape = len(array_shape)
    # Make 10 attempts with random numbers
    for _ in range(10):
        random_numbers = rng.random(random_number_shape)
        raw_inputs = random_numbers * array_bounds
        if has_units:
            inputs = raw_inputs * units
        else:
            inputs = raw_inputs
        expected_ravel = _evaluate_ravel(array_shape, raw_inputs, order)
        ravel_value = ravel(*inputs)
        unraveled_values = ravel.inverse(ravel_value)
        expected_unravel = _evaluate_unravel(array_shape, expected_ravel, order)
        round_trip = ravel.inverse.inverse(*inputs)
        if has_units:
            assert np.allclose(ravel_value, expected_ravel * units)
            assert np.allclose(unraveled_values, expected_unravel * units)
            assert np.allclose(round_trip, expected_ravel * units)
        else:
            assert np.allclose(ravel_value, expected_ravel)
            assert np.allclose(unraveled_values, expected_unravel)
            assert np.allclose(round_trip, expected_ravel)

@pytest.mark.parametrize("ndim", [pytest.param(2, id='2D'), pytest.param(3, id='3D')])
@pytest.mark.parametrize("has_units", [pytest.param(True, id="With Units"), pytest.param(False, id="Without Units")])
@pytest.mark.parametrize("input_type", [pytest.param("array", id="Array Inputs"), pytest.param("scalar", id="Scalar Inputs")])
def test_raveled_tabular1d(ndim, has_units, input_type):
    rng = default_rng()
    array_shape = rng.integers(1, 21, ndim)
    array_bounds = array_shape - 1
    ravel = Ravel(array_shape)
    nelem = np.prod(array_shape)
    values = np.arange(nelem)
    units = u.pix
    if has_units:
        values *= units
    lut_values = values
    tabular = Tabular1D(
        values,
        lut_values,
        bounds_error=False,
        fill_value=np.nan,
        method="linear",
    )
    raveled_tab = ravel | tabular
    if input_type == "array":
        # adding the new axis onto array_bounds makes broadcasting work below
        array_bounds = array_bounds[:, np.newaxis]
        # use 5 as an arbitrary number of inputs
        random_number_shape = len(array_shape), 5
    else:
        random_number_shape = len(array_shape)
    # Make 10 attempts with random numbers
    for _ in range(10):
        random_numbers = rng.random(random_number_shape)
        raw_inputs = random_numbers * array_bounds
        if has_units:
            inputs = tuple(raw_inputs * units)
        else:
            inputs = tuple(raw_inputs)
        expected_ravel = _evaluate_ravel(array_shape, raw_inputs)
        expected_unravel = _evaluate_unravel(array_shape, expected_ravel)
        if has_units:
            assert np.allclose(raveled_tab(*inputs), expected_ravel * units)
            assert np.allclose(raveled_tab.inverse(expected_ravel * units), expected_unravel * units)
            assert np.allclose(raveled_tab.inverse.inverse(*inputs), expected_ravel * units)
        else:
            assert np.allclose(raveled_tab(*inputs), expected_ravel)
            assert np.allclose(raveled_tab.inverse(expected_ravel), expected_unravel)
            assert np.allclose(raveled_tab.inverse.inverse(*inputs), expected_ravel)

@pytest.mark.parametrize("ndim", [pytest.param(2, id='2D'), pytest.param(3, id='3D')])
@pytest.mark.parametrize("order", ["C", "F"])
def test_ravel_ordering(ndim, order):
    rng = default_rng()
    array_shape = rng.integers(2, 21, ndim)
    array_bounds = tuple(np.array(array_shape) - 1)
    ravel = Ravel(array_shape, order=order)
    nelem = np.prod(array_shape)
    values = np.arange(nelem).reshape(array_shape, order=order)
    # Make 10 attempts with random numbers
    for _ in range(10):
        inputs = rng.integers(0, array_bounds, len(array_shape))
        ravel_value = ravel(*inputs)
        assert int(ravel_value) == values[tuple(inputs)]


@pytest.mark.parametrize("ndim", [pytest.param(2, id='2D'), pytest.param(3, id='3D')])
@pytest.mark.parametrize("order", ["C", "F"])
def test_ravel_repr(ndim, order):
    rng = default_rng()
    array_shape = tuple(rng.integers(1, 21, ndim))
    ravel = Ravel(array_shape, order=order)
    unravel = ravel.inverse
    assert str(array_shape) in repr(ravel) and order in repr(ravel)
    assert str(array_shape) in repr(unravel) and order in repr(unravel)


@pytest.mark.parametrize("array_shape", [(0, 1), (1, 0), (1,)])
@pytest.mark.parametrize("ravel", [Ravel, Unravel])
def test_ravel_bad_array_shape(array_shape, ravel):
    with pytest.raises(ValueError) as e:
        ravel(array_shape)

@pytest.mark.parametrize("order", ["A", "B"])
@pytest.mark.parametrize("ravel", [Ravel, Unravel])
def test_ravel_bad_order(order, ravel):
    array_shape=(2, 2, 2)
    with pytest.raises(ValueError) as e:
        ravel(array_shape, order)
