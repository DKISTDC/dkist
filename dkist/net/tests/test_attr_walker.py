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


def test_or_instrument(query_or_instrument):
    walker.create(query_or_instrument)
