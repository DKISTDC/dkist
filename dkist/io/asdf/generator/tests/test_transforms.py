
import pytest

import astropy.units as u
import gwcs.coordinate_frames as cf
from astropy.io import fits
from astropy.modeling import Model, models
from astropy.time import Time

from dkist.io.asdf.generator.transforms import (linear_spectral_model, linear_time_model,
                                                spatial_model_from_header,
                                                spectral_model_from_framewave,
                                                time_model_from_date_obs)


@pytest.fixture
def wcs(transform_builder):
    return transform_builder.gwcs


def test_reset(transform_builder):
    transform_builder._i = 2
    transform_builder.reset()
    assert transform_builder._i == 0


def test_transform(transform_builder):
    assert isinstance(transform_builder.transform, Model)


def test_frames(transform_builder):
    frames = transform_builder.frames
    assert all([isinstance(frame, cf.CoordinateFrame) for frame in frames])


def test_input_name_ordering(wcs):
    # Check the ordering of the input and output frames
    allowed_pixel_names = (('spatial x', 'spatial y', 'wavelength position', 'scan number',
                            'stokes'), ('wavelength', 'slit position', 'raster position',
                                        'scan number', 'stokes'))
    assert wcs.input_frame.axes_names in allowed_pixel_names


def test_output_name_ordering(wcs):
    allowed_world_names = (('longitude', 'latitude', 'wavelength', 'time', 'stokes'),
                           ('wavelength', 'latitude', 'longitude', 'time', 'stokes'))
    assert wcs.output_frame.axes_names in allowed_world_names


def test_output_frames(wcs):
    allowed_frame_orders = ((cf.CelestialFrame, cf.SpectralFrame, cf.TemporalFrame, cf.StokesFrame),
                            (cf.SpectralFrame, cf.CelestialFrame, cf.TemporalFrame, cf.StokesFrame))
    types = tuple((type(frame) for frame in wcs.output_frame.frames))
    assert types in allowed_frame_orders


def test_transform_models(wcs):
    # Test that there is one lookup table and two linear models for both the
    # wcses
    sms = wcs.forward_transform._leaflist
    smtypes = [type(m) for m in sms]
    assert sum(mt is models.Linear1D for mt in smtypes) == 2
    assert sum(mt is models.Tabular1D for mt in smtypes) == 1


def first_header(header_filenames):
    return fits.getheader(header_filenames[0])


def test_spatial_model(header_filenames):
    spatial = spatial_model_from_header(first_header(header_filenames))
    assert isinstance(spatial, Model)


def test_spatial_model_fail(header_filenames):
    header = first_header(header_filenames)
    header['CTYPE2'] = 'WAVE'
    with pytest.raises(ValueError):
        spatial_model_from_header(header)


def test_linear_spectral():
    lin = linear_spectral_model(10*u.nm, 0*u.nm)
    assert isinstance(lin, models.Linear1D)
    assert u.allclose(lin.slope, 10*u.nm/u.pix)
    assert u.allclose(lin.intercept, 0*u.nm)


def test_linear_time():
    lin = linear_time_model(10*u.s)
    assert isinstance(lin, models.Linear1D)
    assert u.allclose(lin.slope, 10*u.s/u.pix)
    assert u.allclose(lin.intercept, 0*u.s)


def test_time_from_dateobs(header_filenames):
    date_obs = [fits.getheader(f)['DATE-OBS'] for f in header_filenames]
    time = time_model_from_date_obs(date_obs)
    assert isinstance(time, models.Linear1D)


def test_time_from_dateobs_lookup(header_filenames):
    date_obs = [fits.getheader(f)['DATE-OBS'] for f in header_filenames]
    date_obs[5] = (Time(date_obs[5]) + 10*u.s).isot
    time = time_model_from_date_obs(date_obs)
    assert isinstance(time, models.Tabular1D)


def test_spectral_framewave(header_filenames):
    head = first_header(header_filenames)

    # Skip the VISP headers
    if "FRAMEWAV" not in head:
        return

    nwave = head['DNAXIS3']
    framewave = [fits.getheader(h)['FRAMEWAV'] for h in header_filenames]

    m = spectral_model_from_framewave(framewave[:nwave])
    assert isinstance(m, models.Linear1D)

    m2 = spectral_model_from_framewave(framewave)
    assert isinstance(m2, models.Tabular1D)
