"""
Hypothesis strategies for testing the DKIST client.
"""
import datetime

import hypothesis.strategies as st
from hypothesis import HealthCheck, assume, settings

import astropy.units as u
from astropy.time import Time
from sunpy.net import attr
from sunpy.net import attrs as a
from sunpy.net.attr import AttrAnd
from sunpy.net.tests.strategies import TimeDelta, Times, time_attr

from dkist.net import DKISTDatasetClient
from dkist.net.attr_walker import walker


def _generate_from_register_values(attr_type):
    possible_values = DKISTDatasetClient.register_values()[attr_type]
    possible_values = list(map(lambda x: x[0], possible_values))

    return st.builds(attr_type, st.sampled_from(possible_values))


def _supported_attr_types():
    attr_types = list(walker.applymm.registry)
    attr_types.remove(object)
    attr_types.remove(AttrAnd)
    attr_types.remove(a.dkist.BoundingBox)
    return attr_types


@st.composite
def _browse_movie(draw):
    return a.dkist.BrowseMovie(**draw(st.dictionaries(st.sampled_from(('movieurl', 'movieobjectkey')),
                               st.text(), min_size=1)))


def _unit_range(attr_type):
    unit = list(attr_type.__init__.__annotations__.values())
    unit = unit[0] if unit else u.one

    # Attrs which have unit decorations not type decorations need special
    # handling or else hypothesis dies.
    if attr_type in (a.Wavelength, a.dkist.SpectralSampling):
        unit = u.nm

    if attr_type is a.dkist.SpatialSampling:
        unit = u.arcsec / u.pix

    if attr_type is a.dkist.TemporalSampling:
        unit = u.s

    @st.composite
    def aunit(draw, number=st.floats(allow_nan=False, allow_infinity=False, min_value=1, max_value=1e10)):
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


for attr_type in DKISTDatasetClient.register_values():
    st.register_type_strategy(attr_type, _generate_from_register_values)

st.register_type_strategy(a.Time, time_attr())
st.register_type_strategy(a.Wavelength, _unit_range)
st.register_type_strategy(a.dkist.SpectralSampling, _unit_range)
st.register_type_strategy(a.dkist.TemporalSampling, _unit_range)
st.register_type_strategy(a.dkist.SpatialSampling, _unit_range)
st.register_type_strategy(a.dkist.BrowseMovie, _browse_movie())
st.register_type_strategy(a.dkist.FriedParameter, _unit_range)
st.register_type_strategy(a.dkist.PolarimetricAccuracy, _unit_range)
st.register_type_strategy(a.dkist.ExposureTime, _unit_range)
st.register_type_strategy(a.dkist.EmbargoEndTime, _embargo_end())

@settings(suppress_health_check=[HealthCheck.too_slow])
@st.composite
def query_and(draw, stattrs=st.lists(st.sampled_from(_supported_attr_types()),
                                     min_size=1, unique=True)):
    """
    Generate a AttrAnd query.
    """
    attr_types = draw(stattrs)
    query_attrs = list(map(draw, map(st.from_type, attr_types)))
    assume(not(len(query_attrs) == 1 and isinstance(query_attrs[0], a.Time)))
    return attr.and_(*query_attrs)


@settings(suppress_health_check=[HealthCheck.too_slow])
@st.composite
def query_or(draw, stattrs=st.lists(st.sampled_from(_supported_attr_types()),
                                    min_size=1, unique=True)):
    """
    Just OR a lot of attrs together.
    """
    attr_types = draw(stattrs)
    query_attrs = list(map(draw, map(st.from_type, attr_types)))
    assume(not(any(isinstance(q, a.Time) for q in query_attrs)))
    return attr.or_(*query_attrs)


@settings(suppress_health_check=[HealthCheck.too_slow])
@st.composite
def query_or_composite(draw, qands=st.lists(query_and(), min_size=2, max_size=5)):
    """
    Make a more realistic OR of ANDs.
    """
    return attr.or_(*draw(qands))
