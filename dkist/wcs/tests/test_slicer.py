import numpy as np
import pytest

import asdf
import astropy.units as u
import gwcs.coordinate_frames as cf
from astropy.coordinates import SkyCoord
from astropy.modeling.models import Identity
from astropy.time import Time
from gwcs import WCS
from sunpy.coordinates.frames import Helioprojective

from dkist.conftest import spatial_like_model
from dkist.data.test import rootdir
from dkist.wcs.slicer import GWCSSlicer

# Some fixtures used in this file are defined in conftest.py


def gwcs_5d_object():
    with asdf.open(str(rootdir / "5d_gwcs.asdf")) as f:
        return f.tree['gwcs']


@pytest.fixture
def gwcs_5d():
    return gwcs_5d_object()


def gwcs_3d_object():
    detector_frame = cf.CoordinateFrame(
        name="detector",
        naxes=3,
        axes_order=(0, 1, 2),
        axes_type=("pixel", "pixel", "pixel"),
        axes_names=("x", "y", "z"),
        unit=(u.pix, u.pix, u.pix))

    sky_frame = cf.CelestialFrame(reference_frame=Helioprojective(), name='hpc')
    spec_frame = cf.SpectralFrame(name="spectral", axes_order=(2, ), unit=u.nm)
    out_frame = cf.CompositeFrame(frames=(sky_frame, spec_frame))

    return WCS(forward_transform=spatial_like_model(),
               input_frame=detector_frame, output_frame=out_frame)


@pytest.fixture
def gwcs_3d():
    return gwcs_3d_object()


def gwcs_1d_object():
    detector_frame = cf.CoordinateFrame(
        name="detector",
        naxes=1,
        axes_order=(0, ),
        axes_type=("pixel"),
        axes_names=("x"),
        unit=(u.pix))

    spec_frame = cf.SpectralFrame(name="spectral", axes_order=(2, ), unit=u.nm)

    return WCS(forward_transform=Identity(1), input_frame=detector_frame, output_frame=spec_frame)


@pytest.fixture
def gwcs_1d():
    return gwcs_1d_object()


@pytest.fixture
def slicer_1d():
    return GWCSSlicer(gwcs_1d_object(), pixel_order=False)


@pytest.fixture
def slicer_3d():
    return GWCSSlicer(gwcs_3d_object(), pixel_order=False)


@pytest.fixture
def slicer_5d():
    return GWCSSlicer(gwcs_5d_object(), pixel_order=False)


def test_slicer_init(gwcs_3d, gwcs_1d):
    for gwcs in (gwcs_1d, gwcs_3d):
        slc = GWCSSlicer(gwcs)
        assert isinstance(slc, GWCSSlicer)
        assert slc.gwcs is gwcs

        slc = GWCSSlicer(gwcs, copy=True)
        assert isinstance(slc, GWCSSlicer)
        assert slc.gwcs is not gwcs


def test_get_axes_map(slicer_3d):
    amap = slicer_3d._get_axes_map(slicer_3d._get_frames())
    assert len(amap) == 3
    assert amap[0] is amap[1]
    assert amap[2] is not amap[1]
    assert amap[2] is not amap[0]


def test_new_output_frame(slicer_1d, slicer_3d):
    assert slicer_3d._new_output_frame(tuple()) is not slicer_1d.gwcs.output_frame

    new_frame = slicer_3d._new_output_frame(tuple())
    assert isinstance(new_frame, cf.CompositeFrame)
    assert len(new_frame.frames) == 2

    new_frame = slicer_3d._new_output_frame((2, ))
    assert isinstance(new_frame, cf.CoordinateFrame)


def test_simple_slices(slicer_3d):
    sl, _ = slicer_3d[:, :, :]
    assert sl is slicer_3d.gwcs
    outs = sl(10 * u.pix, 10 * u.pix, 10 * u.pix)
    assert len(outs) == 3
    sl.invert(*outs)


def test_simple_slices2(slicer_3d):
    sl, _ = slicer_3d[:, :, 0]
    assert sl.forward_transform.n_inputs == 2
    assert isinstance(sl.output_frame, cf.CoordinateFrame)
    outs = sl(10 * u.pix, 10 * u.pix)
    assert len(outs) == 2
    sl.invert(*outs)


def test_simple_slices3(slicer_3d):
    sl, _ = slicer_3d[:, 10, :]
    assert sl.forward_transform.n_inputs == 2
    assert sl.forward_transform.n_outputs == 3
    assert isinstance(sl.output_frame, cf.CompositeFrame)
    outs = sl(10 * u.pix, 10 * u.pix)
    assert len(outs) == 3
    sl.invert(*outs)


def test_simple_slices4(slicer_3d):
    sl, _ = slicer_3d[10]
    assert sl.forward_transform.n_inputs == 2
    assert sl.forward_transform.n_outputs == 3
    assert isinstance(sl.output_frame, cf.CompositeFrame)
    outs = sl(10 * u.pix, 10 * u.pix)
    assert len(outs) == 3
    sl.invert(*outs)


def test_simple_slices5(slicer_3d):
    sl, _ = slicer_3d[10:]
    assert sl.forward_transform.n_inputs == 3
    assert sl.forward_transform.n_outputs == 3
    assert isinstance(sl.output_frame, cf.CompositeFrame)
    outs = sl(10 * u.pix, 10 * u.pix, 10 * u.pix)
    assert len(outs) == 3
    sl.invert(*outs)


def test_error_step(slicer_3d):
    with pytest.raises(ValueError):
        slicer_3d[::2]


def test_error_type(slicer_3d):
    with pytest.raises(ValueError):
        slicer_3d["laksjdkslja"]


def test_roundtrip(slicer_3d):
    wcs, _ = slicer_3d[10:, 10, 10]
    w = wcs(10 * u.pix, with_units=True)
    assert isinstance(w, SkyCoord)
    p = wcs.invert(w, with_units=True)
    assert len(p) == 2


def test_array_call(slicer_3d):
    """
    Test that FixedInputs works with array inputs.
    """
    inp = [np.linspace(0, 10) * u.pix] * 3
    # Sanity check.
    slicer_3d.gwcs(*inp)

    wcs2, _ = slicer_3d[10]
    x, y, z = wcs2(*inp[1:])


# - Slice out both spatial dimensions


def test_5d_both_spatial(slicer_5d):
    wcs, _ = slicer_5d[0, 0, :, 0, 0]
    assert wcs.forward_transform.n_inputs == 1
    assert u.allclose(wcs((0, 1, 2) * u.pix, with_units=True),
                      [854.1105, 854.121, 854.1315] * u.nm)


# - Slice out all of the stokes axis (Table)


def test_5d_stokes_None(slicer_5d):
    wcs, _ = slicer_5d[0, 0, 0, 0, :]
    assert wcs.forward_transform.n_inputs == 1
    stokes = wcs(range(4) * u.pix, with_units=True)
    assert isinstance(stokes, np.ndarray)
    assert list(stokes) == ['I', 'Q', 'U', 'V']


# - Slice out a range in the stokes axis (Table)


def test_5d_stokes_range(slicer_5d):
    wcs, _ = slicer_5d[0, 0, 0, 0, 1:3]
    assert wcs.forward_transform.n_inputs == 1
    stokes = wcs(range(3) * u.pix, with_units=True)
    assert isinstance(stokes, np.ndarray)
    assert list(stokes) == ['Q', 'U', 'V']


# - Slice out one of the coupled axis


def test_5d_spatial_split(slicer_5d):
    wcs, _ = slicer_5d[0, :, 0, :, 0]
    assert wcs.forward_transform.n_inputs == 2
    assert wcs.forward_transform.n_outputs == 3
    coords = wcs(0 * u.pix, 0 * u.pix, with_units=True)
    assert isinstance(coords[0], SkyCoord)
    assert u.allclose(coords[0].Tx, -956.528 * u.arcsec)
    assert u.allclose(coords[0].Ty, 817.281 * u.arcsec)
    assert isinstance(coords[1], Time)
    np.testing.assert_allclose(coords[1].jd, 2459849.5946575697)
