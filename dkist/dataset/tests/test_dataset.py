import os

import numpy as np
import pytest
import dask.array as da

import gwcs
import astropy.units as u
import gwcs.coordinate_frames as cf
import astropy.modeling.models as m
from astropy.tests.helper import assert_quantity_allclose
from sunpy.coordinates.frames import Helioprojective

from dkist.dataset import Dataset
from dkist.data.test import rootdir


@pytest.fixture
def array():
    shape = np.random.randint(1, 100, size=2)
    x = np.ones(shape) + 10  # Make sure we can actually slice the thing later
    return da.from_array(x, tuple(shape))


@pytest.fixture
def identity_gwcs():
    """
    A simple 1-1 gwcs that converts from pixels to arcseconds
    """
    identity = m.Multiply(1*u.arcsec/u.pixel) & m.Multiply(1*u.arcsec/u.pixel)
    sky_frame = cf.CelestialFrame(axes_order=(0, 1), name='helioprojective',
                                  reference_frame=Helioprojective(obstime="2018-01-01"))
    detector_frame = cf.CoordinateFrame(name="detector", naxes=2,
                                        axes_order=(0, 1),
                                        axes_type=("pixel", "pixel"),
                                        axes_names=("x", "y"),
                                        unit=(u.pix, u.pix))
    return gwcs.wcs.WCS(forward_transform=identity, output_frame=sky_frame, input_frame=detector_frame)


@pytest.fixture
def identity_gwcs_3d():
    """
    A simple 1-1 gwcs that converts from pixels to arcseconds
    """
    identity = m.Multiply(1*u.arcsec/u.pixel) & m.Multiply(1*u.arcsec/u.pixel) & m.Multiply(1*u.nm/u.pixel)
    sky_frame = cf.CelestialFrame(axes_order=(0, 1), name='helioprojective',
                                  reference_frame=Helioprojective(obstime="2018-01-01"))
    wave_frame = cf.SpectralFrame(axes_order=(2, ), unit=u.nm)

    frame = cf.CompositeFrame([sky_frame, wave_frame])

    detector_frame = cf.CoordinateFrame(name="detector", naxes=3,
                                        axes_order=(0, 1, 2),
                                        axes_type=("pixel", "pixel", "pixel"),
                                        axes_names=("x", "y", "z"), unit=(u.pix, u.pix, u.pix))

    return gwcs.wcs.WCS(forward_transform=identity, output_frame=frame, input_frame=detector_frame)


@pytest.fixture
def identity_gwcs_4d():
    """
    A simple 1-1 gwcs that converts from pixels to arcseconds
    """
    identity = (m.Multiply(1*u.arcsec/u.pixel) & m.Multiply(1*u.arcsec/u.pixel) &
                m.Multiply(1*u.nm/u.pixel) & m.Multiply(1*u.nm/u.pixel))
    sky_frame = cf.CelestialFrame(axes_order=(0, 1), name='helioprojective',
                                  reference_frame=Helioprojective(obstime="2018-01-01"))
    wave_frame = cf.SpectralFrame(axes_order=(2, ), unit=u.nm)
    time_frame = cf.TemporalFrame(axes_order=(3, ), unit=u.s)

    frame = cf.CompositeFrame([sky_frame, wave_frame, time_frame])

    detector_frame = cf.CoordinateFrame(name="detector", naxes=4,
                                        axes_order=(0, 1, 2, 3),
                                        axes_type=("pixel", "pixel", "pixel", "pixel"),
                                        axes_names=("x", "y", "z", "s"), unit=(u.pix, u.pix, u.pix, u.pix))

    return gwcs.wcs.WCS(forward_transform=identity, output_frame=frame, input_frame=detector_frame)


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
    x = np.ones(shape)
    array = da.from_array(x, tuple(shape))

    return Dataset(array, wcs=identity_gwcs_3d)


@pytest.fixture
def dataset_4d(identity_gwcs_4d):
    shape = (50, 60, 70, 80)
    x = np.ones(shape)
    array = da.from_array(x, tuple(shape))

    return Dataset(array, wcs=identity_gwcs_4d)


def test_repr(dataset, dataset_3d):
    r = repr(dataset)
    assert str(dataset.data) in r
    r = repr(dataset_3d)
    assert str(dataset_3d.data) in r


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
    arr = dataset_3d.crop_by_coords((5*u.arcsec, 5*u.arcsec, 5*u.nm),
                                    (9*u.arcsec, 9*u.arcsec, 9*u.nm))

    da_crop = dataset_3d.data[5:10, 5:10, 5:10]
    assert arr.data.shape == da_crop.shape
    assert np.allclose(arr.data, da_crop)


def test_crop_by_coords_units(dataset_3d):
    arr = dataset_3d.crop_by_coords((5, 5, 5),
                                    (9, 9, 9),
                                    (u.arcsec, u.arcsec, u.nm))

    da_crop = dataset_3d.data[5:10, 5:10, 5:10]
    assert arr.data.shape == da_crop.shape
    assert np.allclose(arr.data, da_crop)


def test_crop_by_coords_bad_args(dataset_3d):
    with pytest.raises(TypeError):
        dataset_3d.crop_by_coords((5, 5)*u.arcsec, (5, 5))


def test_crop_by_coords_bad_units(dataset_3d):
    with pytest.raises(ValueError):
        dataset_3d.crop_by_coords((5, 5, 5), (9, 9, 9), units=(u.pix, u.pix))


def test_load_from_directory():
    ds = Dataset.from_directory(os.path.join(rootdir, 'EIT'))
    assert isinstance(ds.data, da.Array)
    assert isinstance(ds.wcs, gwcs.WCS)
    assert_quantity_allclose(ds.dimensions, (11, 128, 128)*u.pix)


def test_from_directory_no_asdf(tmpdir):
    with pytest.raises(ValueError) as e:
        Dataset.from_directory(tmpdir)
        assert "No asdf file found" in str(e)


def test_from_not_directory():
    with pytest.raises(ValueError) as e:
        Dataset.from_directory(rootdir/"notadirectory")
        assert "directory argument" in str(e)


def test_from_directory_not_dir():
    with pytest.raises(ValueError) as e:
        Dataset.from_directory(os.path.join(rootdir, 'EIT', 'eit_2004-03-01T00:00:10.515000.asdf'))
        assert "must be a directory" in str(e)


def test_no_wcs_slice(dataset):
    dataset._wcs = None
    ds = dataset[3, 0]
    assert ds.wcs is None


def test_crop_few_slices(dataset_4d):
    sds = dataset_4d[0, 0]
    assert len(sds.wcs.input_frame.axes_order)
