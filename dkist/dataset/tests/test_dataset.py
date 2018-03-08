import pytest

import numpy as np
import dask.array as da

import astropy.units as u
import astropy.modeling.models as m
from astropy.tests.helper import assert_quantity_allclose

import gwcs
import gwcs.coordinate_frames as cf

from sunpy.coordinates.frames import Helioprojective


from dkist.dataset import Dataset


@pytest.fixture
def array():
    shape = np.random.randint(100, size=2)
    x = np.random.random(shape)
    return da.from_array(x, tuple(shape))


@pytest.fixture
def identity_gwcs():
    """
    A simple 1-1 gwcs that converts from pixels to arcseconds
    """
    identity = m.Scale(1*u.arcsec/u.pixel) & m.Scale(1*u.arcsec/u.pixel)
    sky_frame = cf.CelestialFrame(axes_order=(0, 1), name='helioprojective',
                                  reference_frame=Helioprojective(obstime="2018-01-01"))
    return gwcs.wcs.WCS(forward_transform=identity, output_frame=sky_frame)


@pytest.fixture
def identity_gwcs_3d():
    """
    A simple 1-1 gwcs that converts from pixels to arcseconds
    """
    identity = m.Scale(1*u.arcsec/u.pixel) & m.Scale(1*u.arcsec/u.pixel) & m.Scale(1*u.nm/u.pixel)
    sky_frame = cf.CelestialFrame(axes_order=(0, 1), name='helioprojective',
                                  reference_frame=Helioprojective(obstime="2018-01-01"))
    wave_frame = cf.SpectralFrame(axes_order=(2, ), unit=u.nm)

    frame = cf.CompositeFrame([sky_frame, wave_frame])
    return gwcs.wcs.WCS(forward_transform=identity, output_frame=frame)


@pytest.fixture
def dataset(array, identity_gwcs):
    ds = Dataset(array, wcs=identity_gwcs)
    # Sanity checks
    assert ds.data is array
    assert ds.wcs is identity_gwcs
    return ds


@pytest.fixture
def dataset_3d(identity_gwcs_3d):
    shape = (50, 50, 50)
    x = np.random.random(shape)
    array = da.from_array(x, tuple(shape))

    return Dataset(array, wcs=identity_gwcs_3d)


def test_repr(dataset):
    r = repr(dataset)
    assert str(dataset.data) in r
    assert repr(dataset.wcs)[1:-1] in r


def test_wcs_roundtrip(dataset):
    p = (10*u.pixel, 10*u.pixel)
    w = dataset.pixel_to_world(*p)
    p2 = dataset.world_to_pixel(w)
    assert_quantity_allclose(p, p2)


def test_wcs_roundtrip_3d(dataset_3d):
    p = (10*u.pixel, 10*u.pixel, 10*u.pixel)
    w = dataset_3d.pixel_to_world(*p)
    p2 = dataset_3d.world_to_pixel(*w)
    assert_quantity_allclose(p[:2], p2[:2])
    assert_quantity_allclose(p[2], p2[2])


def test_dimensions(dataset, dataset_3d):
    for ds in [dataset, dataset_3d]:
        assert_quantity_allclose(ds.dimensions, ds.data.shape*u.pix)


def test_crop_by_coords(dataset_3d):
    arr = dataset_3d.crop_by_coords((5, 5, 5)*u.arcsec, (5, 5, 5)*u.arcsec)
    da_crop = dataset_3d.data[5:10, 5:10, 5:10]
    assert arr.shape == da_crop.shape
    assert np.allclose(arr, da_crop)


def test_crop_by_coords_bad_args(dataset_3d):
    with pytest.raises(ValueError):
        dataset_3d.crop_by_coords((5, 5)*u.arcsec, (5, 5)*u.arcsec)
