"""
Hypothesis strategies for testing the DKIST client.
"""
import datetime

import hypothesis.strategies as st
from hypothesis import assume

import astropy.units as u
from astropy.time import Time
from sunpy.net import attrs as a
from sunpy.net.attr import AttrAnd
from sunpy.net.tests.strategies import TimeDelta, Times, time_attr

from dkist.net import DKISTDatasetClient
from dkist.net.attr_walker import walker


@st.composite
def _wavelength(draw):
    return draw(st.floats(min_value=1, max_value=1e9)) * u.pm


def _generate_from_register_values(attr_type):
    possible_values = DKISTDatasetClient.register_values()[DKISTDatasetClient][attr_type]
    possible_values = list(map(lambda x: x[0], possible_values))

    return st.builds(attr_type, st.sampled_from(possible_values))


def _supported_attr_types():
    attr_types = list(walker.applymm.registry)
    attr_types.remove(object)
    attr_types.remove(AttrAnd)
    return attr_types


@st.composite
def _browse_movie(draw):
    return a.dkist.BrowseMovie(**draw(st.dictionaries(st.sampled_from(('movieurl', 'movieobjectkey')),
                               st.text(), min_size=1)))


def _unit_range(attr_type):
    unit = list(attr_type.__init__.__annotations__.values())
    unit = unit[0] if unit else u.one
    if attr_type is a.Wavelength:
        unit = u.nm

    @st.composite
    def aunit(draw, number=st.floats(allow_nan=False, allow_infinity=False, min_value=1)):
        return draw(number) * unit

    return st.builds(attr_type, aunit(), aunit())

@st.composite
def _embargo_end(draw, time=Times(
                 max_value=datetime.datetime(datetime.datetime.utcnow().year, 1, 1, 0, 0),
                 min_value=datetime.datetime(1981, 1, 1, 0, 0)),
                 delta=TimeDelta()):
    t1 = draw(time)
    t2 = t1 + draw(delta)

    assume(t2 < Time.now())

    return a.dkist.EmbargoEndTime(t1, t2)


for attr_type in DKISTDatasetClient.register_values()[DKISTDatasetClient]:
    st.register_type_strategy(attr_type, _generate_from_register_values)

st.register_type_strategy(a.Time, time_attr())
st.register_type_strategy(a.Wavelength, _unit_range)
st.register_type_strategy(a.dkist.BrowseMovie, _browse_movie())
st.register_type_strategy(a.dkist.FriedParameter, _unit_range)
st.register_type_strategy(a.dkist.PolarimetricAccuracy, _unit_range)
st.register_type_strategy(a.dkist.ExposureTime, _unit_range)
st.register_type_strategy(a.dkist.EmbargoEndTime, _embargo_end())
