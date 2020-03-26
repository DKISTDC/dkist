import dask.array as da
import numpy as np
import pytest

import astropy.modeling.models as m
import astropy.units as u
import gwcs
import gwcs.coordinate_frames as cf
from astropy.table import Table
from astropy.time import Time
from sunpy.coordinates.frames import Helioprojective

from dkist.dataset import Dataset
from dkist.io import AstropyFITSLoader, DaskFITSArrayContainer
from dkist.io.asdf.generator.transforms import generate_lookup_table


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
                                  reference_frame=Helioprojective(obstime="2018-01-01"),
                                  unit=(u.arcsec, u.arcsec))
    detector_frame = cf.CoordinateFrame(name="detector", naxes=2,
                                        axes_order=(0, 1),
                                        axes_type=("pixel", "pixel"),
                                        axes_names=("x", "y"),
                                        unit=(u.pix, u.pix))
    wcs = gwcs.wcs.WCS(forward_transform=identity, output_frame=sky_frame, input_frame=detector_frame)
    wcs.pixel_shape = (10, 20)
    wcs.array_shape = wcs.pixel_shape[::-1]
    return wcs


@pytest.fixture
def identity_gwcs_3d():
    """
    A simple 1-1 gwcs that converts from pixels to arcseconds
    """
    identity = (m.Multiply(1 * u.arcsec / u.pixel) &
                m.Multiply(1 * u.arcsec / u.pixel) &
                m.Multiply(1 * u.nm / u.pixel))

    sky_frame = cf.CelestialFrame(axes_order=(0, 1), name='helioprojective',
                                  reference_frame=Helioprojective(obstime="2018-01-01"),
                                  axes_names=("longitude", "latitude"),
                                  unit=(u.arcsec, u.arcsec))
    wave_frame = cf.SpectralFrame(axes_order=(2, ), unit=u.nm, axes_names=("wavelength",))

    frame = cf.CompositeFrame([sky_frame, wave_frame])

    detector_frame = cf.CoordinateFrame(name="detector", naxes=3,
                                        axes_order=(0, 1, 2),
                                        axes_type=("pixel", "pixel", "pixel"),
                                        axes_names=("x", "y", "z"), unit=(u.pix, u.pix, u.pix))

    wcs = gwcs.wcs.WCS(forward_transform=identity, output_frame=frame, input_frame=detector_frame)
    wcs.pixel_shape = (10, 20, 30)
    wcs.array_shape = wcs.pixel_shape[::-1]

    return wcs


@pytest.fixture
def identity_gwcs_3d_temporal():
    """
    A simple 1-1 gwcs that converts from pixels to arcseconds
    """
    identity = (m.Multiply(1 * u.arcsec / u.pixel) &
                m.Multiply(1 * u.arcsec / u.pixel) &
                m.Multiply(1 * u.s / u.pixel))

    sky_frame = cf.CelestialFrame(axes_order=(0, 1), name='helioprojective',
                                  reference_frame=Helioprojective(obstime="2018-01-01"),
                                  axes_names=("longitude", "latitude"),
                                  unit=(u.arcsec, u.arcsec))
    time_frame = cf.TemporalFrame(Time("2020-01-01T00:00", format="isot", scale="utc"),
                                  axes_order=(2,), unit=u.s)

    frame = cf.CompositeFrame([sky_frame, time_frame])

    detector_frame = cf.CoordinateFrame(name="detector", naxes=3,
                                        axes_order=(0, 1, 2),
                                        axes_type=("pixel", "pixel", "pixel"),
                                        axes_names=("x", "y", "z"), unit=(u.pix, u.pix, u.pix))
    wcs = gwcs.wcs.WCS(forward_transform=identity, output_frame=frame, input_frame=detector_frame)
    wcs.pixel_shape = (10, 20, 30)
    wcs.array_shape = wcs.pixel_shape[::-1]
    return wcs


@pytest.fixture
def identity_gwcs_4d():
    """
    A simple 1-1 gwcs that converts from pixels to arcseconds
    """
    identity = (m.Multiply(1 * u.arcsec/u.pixel) & m.Multiply(1 * u.arcsec/u.pixel) &
                m.Multiply(1 * u.nm/u.pixel) & m.Multiply(1 * u.s/u.pixel))
    sky_frame = cf.CelestialFrame(axes_order=(0, 1), name='helioprojective',
                                  reference_frame=Helioprojective(obstime="2018-01-01"),
                                  unit=(u.arcsec, u.arcsec))
    wave_frame = cf.SpectralFrame(axes_order=(2, ), unit=u.nm)
    time_frame = cf.TemporalFrame(Time("2020-01-01T00:00", format="isot", scale="utc"), axes_order=(3, ), unit=u.s)

    frame = cf.CompositeFrame([sky_frame, wave_frame, time_frame])

    detector_frame = cf.CoordinateFrame(name="detector", naxes=4,
                                        axes_order=(0, 1, 2, 3),
                                        axes_type=("pixel", "pixel", "pixel", "pixel"),
                                        axes_names=("x", "y", "z", "s"),
                                        unit=(u.pix, u.pix, u.pix, u.pix))

    wcs = gwcs.wcs.WCS(forward_transform=identity, output_frame=frame, input_frame=detector_frame)
    wcs.pixel_shape = (10, 20, 30, 40)
    wcs.array_shape = wcs.pixel_shape[::-1]

    return wcs


@pytest.fixture
def identity_gwcs_5d_stokes(identity_gwcs_4d):
    stokes_frame = cf.StokesFrame(axes_order=(4,))
    stokes_model = generate_lookup_table([0, 1, 2, 3] * u.one, interpolation='nearest')
    transform = identity_gwcs_4d.forward_transform
    frame = cf.CompositeFrame(identity_gwcs_4d.output_frame.frames + [stokes_frame])

    detector_frame = cf.CoordinateFrame(name="detector", naxes=5,
                                        axes_order=(0, 1, 2, 3, 4),
                                        axes_type=("pixel", "pixel", "pixel", "pixel", "pixel"),
                                        axes_names=("x", "y", "z", "t", "s"),
                                        unit=(u.pix, u.pix, u.pix, u.pix, u.pix))

    wcs = gwcs.wcs.WCS(forward_transform=transform & stokes_model, output_frame=frame,
                       input_frame=detector_frame)
    wcs.pixel_shape = (10, 20, 30, 40, 4)
    wcs.array_shape = wcs.pixel_shape[::-1]

    return wcs


@pytest.fixture
def dataset(array, identity_gwcs):
    meta = {'bucket': 'data',
            'dataset_id': 'test_dataset',
            'asdf_object_key': 'test_dataset.asdf'}

    identity_gwcs.array_shape = array.shape
    identity_gwcs.pixel_shape = array.shape[::-1]
    ds = Dataset(array, wcs=identity_gwcs, meta=meta, headers=Table())
    # Sanity checks
    assert ds.data is array
    assert ds.wcs is identity_gwcs

    ds._array_container = DaskFITSArrayContainer(['test1.fits'], 0, 'float', array.shape,
                                                 loader=AstropyFITSLoader)

    return ds


@pytest.fixture
def dataset_3d(identity_gwcs_3d):
    shape = (25, 50, 50)
    x = np.ones(shape)
    array = da.from_array(x, tuple(shape))

    identity_gwcs_3d.pixel_shape = array.shape[::-1]
    identity_gwcs_3d.array_shape = array.shape

    return Dataset(array, wcs=identity_gwcs_3d)


@pytest.fixture
def dataset_4d(identity_gwcs_4d):
    shape = (50, 60, 70, 80)
    x = np.ones(shape)
    array = da.from_array(x, tuple(shape))

    identity_gwcs_4d.pixel_shape = array.shape[::-1]
    identity_gwcs_4d.array_shape = array.shape

    return Dataset(array, wcs=identity_gwcs_4d)
