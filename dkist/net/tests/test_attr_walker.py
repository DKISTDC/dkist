import pytest

import astropy.units as u
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


@pytest.fixture(params=da.__all__)
def all_attrs_classes(request):
    return getattr(da, request.param)


def test_walker_single(all_attrs_classes):
    at = None
    value_len = 1

    if issubclass(all_attrs_classes, attr.SimpleAttr):
        at = all_attrs_classes("stokes_parameters")

        if isinstance(at, da.Provider):
            value_len = 0

    elif issubclass(all_attrs_classes, a.Time):
        at = all_attrs_classes("2020/01/01", "2020/01/02")
        value_len = 2

    elif issubclass(all_attrs_classes, attr.Range):
        unit = list(all_attrs_classes.__init__.__annotations__.values())
        unit = unit[0] if unit else u.one
        at = all_attrs_classes(10*unit, 10*unit)
        value_len = 2

    elif issubclass(all_attrs_classes, da.BrowseMovie):
        at = all_attrs_classes(movieurl="klsdjalkjd")

    if not at:
        pytest.skip(f"Not testing {all_attrs_classes!r}")

    params = walker.create(at)
    assert isinstance(params, list)
    assert len(params) == 1
    assert isinstance(params[0], dict)
    assert len(params[0]) == value_len


def test_and_simple(query_and_simple):
    out = walker.create(query_and_simple)
    assert len(out) == 1
    assert isinstance(out, list)
    assert all([isinstance(a, dict) for a in out])

    assert out == [
        {
            "instrumentNames": ["VBI"],
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
            "instrumentNames": ["VBI"],
            "startTimeMin": "2020-06-01T00:00:00.000",
            "endTimeMax": "2020-06-02T00:00:00.000",
        },
        {
            "instrumentNames": ["VISP"],
            "startTimeMin": "2020-06-01T00:00:00.000",
            "endTimeMax": "2020-06-02T00:00:00.000",
        }
    ]
