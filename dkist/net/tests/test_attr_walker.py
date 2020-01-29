import pytest

from sunpy.net import attrs as a

# import dkist.net.attrs as da
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
