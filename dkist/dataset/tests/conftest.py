import dask.array as da
import numpy as np
import pytest

import astropy.modeling.models as m
import astropy.units as u
import gwcs
import gwcs.coordinate_frames as cf
from sunpy.coordinates.frames import Helioprojective

from dkist.dataset import Dataset


@pytest.fixture
def array():
    shape = np.random.randint(10, 100, size=2)
    x = np.ones(shape) + 10
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
    identity = m.Multiply(1 * u.arcsec / u.pixel) & m.Multiply(1 * u.arcsec / u.pixel) & m.Multiply(1 * u.nm / u.pixel)
    sky_frame = cf.CelestialFrame(axes_order=(0, 1), name='helioprojective',
                                  reference_frame=Helioprojective(obstime="2018-01-01"),
                                  axes_names=("longitude", "latitude"))
    wave_frame = cf.SpectralFrame(axes_order=(2, ), unit=u.nm, axes_names=("wavelength",))

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
