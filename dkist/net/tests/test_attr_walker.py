import re

import pytest

import astropy.units as u
from astropy.coordinates import ICRS, SkyCoord
from sunpy.net import attr
from sunpy.net import attrs as a

import dkist.net.attrs as da
from dkist.net.attr_walker import walker


@pytest.fixture
def query_and_simple():
    return a.Instrument("VBI") & a.Time("2020/06/01", "2020/06/02")


@pytest.fixture
def query_or_instrument():
    """
    A query which applies or to array types.
    """
    return (a.Instrument("VBI") | a.Instrument("VISP")) & a.Time("2020/06/01", "2020/06/02")

@pytest.fixture(scope="function")
def boundingbox_params():
    """
    Create possible bounding box input coordinates and args
    for inputs to the bounding box tests.
    """
    bottom_left_icrs = SkyCoord(ICRS(ra=1 * u.deg, dec=2 * u.deg, distance=150000000 * u.km),
                                obstime='2021-01-02T12:34:56')
    top_right_icrs = SkyCoord(ICRS(ra=3 * u.deg, dec=4 * u.deg, distance=150000000 * u.km),
                              obstime='2021-01-02T12:34:56')
    bottom_left_vector_icrs = SkyCoord([ICRS(ra=1 * u.deg, dec=2 * u.deg, distance=150000000 * u.km),
                                        ICRS(ra=3 * u.deg, dec=4 * u.deg, distance=150000000 * u.km)],
                                       obstime='2021-01-02T12:34:56')
    bottom_left = SkyCoord(1 * u.deg, 1 * u.deg, frame='heliographic_stonyhurst', obstime='2021-01-02T12:34:56')
    top_right = SkyCoord(2 * u.deg, 2 * u.deg, frame='heliographic_stonyhurst', obstime='2021-01-02T12:34:56')

    width = 3.4 * u.deg
    height = 1.2 * u.deg

    yield {
        # bottom_left, top_right, width, height
        "bottom left vector icrs": [bottom_left_vector_icrs, None, None, None],
        "bottom left top right icrs": [bottom_left_icrs, top_right_icrs, None, None],
        "bottom left top right": [bottom_left, top_right, None, None],
        "bottom left width height": [bottom_left, None, width, height],
    }

@pytest.fixture(scope="function",
                params=["bottom left vector icrs",
                        "bottom left top right icrs",
                        "bottom left top right",
                        "bottom left width height",],)
def boundingbox_param(request, boundingbox_params):
    yield boundingbox_params[request.param]


def test_walker_single(all_attrs_classes, api_param_names):
    at = None

    if issubclass(all_attrs_classes, da.SpatialSampling):
        at = all_attrs_classes(spatialmin= 1.3 * u.arcsec/u.pix, spatialmax= 1.5 * u.arcsec/u.pix)

    elif issubclass(all_attrs_classes, da.SpectralSampling):
        at = all_attrs_classes(spectralmin=580 * u.nm, spectralmax=590 * u.nm)

    elif issubclass(all_attrs_classes, da.TemporalSampling):
        at = all_attrs_classes(temporalmin= 1 * u.s, temporalmax= 500 * u.s)

    elif issubclass(all_attrs_classes, attr.SimpleAttr):
        at = all_attrs_classes("stokes_parameters")

    elif issubclass(all_attrs_classes, a.Time):
        at = all_attrs_classes("2020/01/01", "2020/01/02")

    elif issubclass(all_attrs_classes, a.Wavelength):
        at = all_attrs_classes(10*u.nm, 20*u.nm)

    elif issubclass(all_attrs_classes, attr.Range):
        unit = list(all_attrs_classes.__init__.__annotations__.values())
        unit = unit[0] if unit else u.one
        at = all_attrs_classes(10*unit, 10*unit)

    elif issubclass(all_attrs_classes, da.BrowseMovie):
        at = all_attrs_classes(movieurl="klsdjalkjd", movieobjectkey="lkajsd")
        api_param_names[all_attrs_classes] = ('browseMovieUrl', 'browseMovieObjectKey')

    elif issubclass(all_attrs_classes, da.BoundingBox):
        bottom_left = SkyCoord([ICRS(ra=1 * u.deg, dec=2 * u.deg, distance=150000000 * u.km),
                                   ICRS(ra=3 * u.deg, dec=4 * u.deg, distance=150000000 * u.km)],
                                  obstime='2021-01-02T12:34:56')
        at = all_attrs_classes(bottom_left=bottom_left)
        api_param_names[all_attrs_classes] = ('rectangleContainingBoundingBox',)


    if not at:
        pytest.skip(f"Not testing {all_attrs_classes!r}")

    params = walker.create(at)
    assert isinstance(params, list)
    assert len(params) == 1
    assert isinstance(params[0], dict)
    assert len(params[0]) == len(api_param_names[all_attrs_classes])
    assert not set(api_param_names[all_attrs_classes]).difference(params[0].keys())


@pytest.mark.parametrize("search,search_type",
                         [
                             ('containing', 'rectangleContainingBoundingBox'),
                             ('contained', 'rectangleContainedByBoundingBox'),
                             ('intersecting', 'rectangleIntersectingBoundingBox'),
                         ]
                         )
def test_boundingbox(search, search_type, boundingbox_param):
    bb_query = da.BoundingBox(bottom_left=boundingbox_param[0], top_right=boundingbox_param[1],
                       width=boundingbox_param[2], height=boundingbox_param[3], search=search)

    out = walker.create(bb_query)
    assert len(out) == 1
    assert all([isinstance(a, dict) for a in out])

    # can't verify exact coordinates, they change a bit
    for key in out[0].keys():
        assert key == search_type

    for value in out[0].values():
        # want to make sure the value is of the format (flt, flt), (flt, flt)
        coordinate_regex = re.compile(r'^(\()(-?\d+)(\.\d+)?(,)(-?\d+)(\.\d+)?(\))(,)(\()(-?\d+)(\.\d+)?(,)(-?\d+)(\.\d+)?(\))$')
        assert coordinate_regex.search(value)

def test_args_browsemovie():
    with pytest.raises(ValueError):
        da.BrowseMovie()


def test_both_physobs():
    params = walker.create(a.Physobs("intensity"))
    assert len(params) == 1
    assert params[0]["hasAllStokes"] is False

    params = walker.create(a.Physobs("stokes_parameters"))
    assert len(params) == 1
    assert params[0]["hasAllStokes"] is True

    params = walker.create(a.Physobs("spectral_axis"))
    assert len(params) == 1
    assert params[0]["hasSpectralAxis"] is True

    params = walker.create(a.Physobs("temporal_axis"))
    assert len(params) == 1
    assert params[0]["hasTemporalAxis"] is True

def test_and_simple(query_and_simple):
    out = walker.create(query_and_simple)
    assert len(out) == 1
    assert isinstance(out, list)
    assert all([isinstance(a, dict) for a in out])

    assert out == [
        {
            "instrumentNames": "VBI",
            "startTimeMin": "2020-06-01T00:00:00.000",
            "endTimeMax": "2020-06-02T00:00:00.000",
        }
    ]


def test_or_instrument(query_or_instrument):
    out = walker.create(query_or_instrument)
    assert len(out) == 2
    assert isinstance(out, list)
    assert all([isinstance(a, dict) for a in out])

    assert out == [
        {
            "instrumentNames": "VBI",
            "startTimeMin": "2020-06-01T00:00:00.000",
            "endTimeMax": "2020-06-02T00:00:00.000",
        },
        {
            "instrumentNames": "VISP",
            "startTimeMin": "2020-06-01T00:00:00.000",
            "endTimeMax": "2020-06-02T00:00:00.000",
        }
    ]
