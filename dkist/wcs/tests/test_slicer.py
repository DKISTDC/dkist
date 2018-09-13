import pytest

import astropy.units as u
import gwcs.coordinate_frames as cf
from gwcs import WCS
from astropy.coordinates import SkyCoord
from astropy.modeling.models import Identity
from sunpy.coordinates.frames import Helioprojective

from dkist.conftest import spatial_like
from dkist.wcs.slicer import GWCSSlicer, FixedParameter


def test_fixed_parameter():
    fp = FixedParameter(1)
    assert fp() == 1
    assert fp.n_inputs == 0
    assert fp.n_outputs == 1

def test_fixed_parameter_inverse():
    fp = FixedParameter(1)
    inv = fp.inverse
    assert isinstance(inv, Identity)
    assert inv.n_inputs == 1


## Some fixtures used in this file are defined in conftest.py

@pytest.fixture
def gwcs_3d():
    detector_frame = cf.CoordinateFrame(name="detector",
                                        naxes=3,
                                        axes_order=(0,1,2),
                                        axes_type=("pixel", "pixel", "pixel"),
                                        axes_names=("x", "y", "z"),
                                        unit=(u.pix, u.pix, u.pix))

    sky_frame = cf.CelestialFrame(reference_frame=Helioprojective(), name='hpc')
    spec_frame = cf.SpectralFrame(name="spectral", axes_order=(2,), unit=u.nm)
    out_frame = cf.CompositeFrame(frames=(sky_frame, spec_frame))

    return WCS(forward_transform=spatial_like(), input_frame=detector_frame, output_frame=out_frame)

@pytest.fixture
def gwcs_1d():
    detector_frame = cf.CoordinateFrame(name="detector",
                                        naxes=1,
                                        axes_order=(0,),
                                        axes_type=("pixel"),
                                        axes_names=("x"),
                                        unit=(u.pix))

    spec_frame = cf.SpectralFrame(name="spectral", axes_order=(2,), unit=u.nm)

    return WCS(forward_transform=Identity(1), input_frame=detector_frame, output_frame=spec_frame)


@pytest.fixture
def slicer_1d():
    return GWCSSlicer(gwcs_1d())


@pytest.fixture
def slicer_3d():
    return GWCSSlicer(gwcs_3d())


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
    assert slicer_1d._new_output_frame(tuple()) is slicer_1d.gwcs.output_frame
    assert slicer_3d._new_output_frame(tuple()) is not slicer_1d.gwcs.output_frame

    new_frame = slicer_3d._new_output_frame(tuple())
    assert isinstance(new_frame, cf.CompositeFrame)
    assert len(new_frame.frames) == 2

    new_frame = slicer_3d._new_output_frame((2,))
    assert isinstance(new_frame, cf.CoordinateFrame)


def test_simple_slices(slicer_3d):
    sl = slicer_3d[:,:,:]
    assert sl is slicer_3d.gwcs

def test_simple_slices2(slicer_3d):
    sl2 = slicer_3d[:,:,0]
    assert sl2.forward_transform.n_inputs == 2
    assert isinstance(sl2.output_frame, cf.CoordinateFrame)

def test_simple_slices3(slicer_3d):
    sl = slicer_3d[:,10,:]
    assert sl.forward_transform.n_inputs == 2
    assert sl.forward_transform.n_outputs == 3
    assert isinstance(sl.output_frame, cf.CompositeFrame)

def test_simple_slices4(slicer_3d):
    sl = slicer_3d[10]
    assert sl.forward_transform.n_inputs == 2
    assert sl.forward_transform.n_outputs == 3
    assert isinstance(sl.output_frame, cf.CompositeFrame)

def test_simple_slices5(slicer_3d):
    sl = slicer_3d[10:]
    assert sl.forward_transform.n_inputs == 3
    assert sl.forward_transform.n_outputs == 3
    assert isinstance(sl.output_frame, cf.CompositeFrame)

def test_error_step(slicer_3d):
    with pytest.raises(ValueError):
        sl = slicer_3d[::2]

def test_error_type(slicer_3d):
    with pytest.raises(ValueError):
        sl = slicer_3d["laksjdkslja"]


def test_roundtrip(slicer_3d):
    wcs = slicer_3d[10:, 10, 10]
    w = wcs(10*u.pix, with_units=True)
    assert isinstance(w, SkyCoord)
    p = wcs.invert(w, with_units=True)
    assert len(p) == 2
