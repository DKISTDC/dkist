from sunpy.net.attr import AttrAnd, AttrOr, AttrWalker, ValueAttr
from sunpy.net.attrs import Instrument, Time, Wavelength

from .attrs import *

walker = AttrWalker()
"""
The DKIST Client walker works by the creator creating a list of dicts, which
become the query parameters to the call to the dataset searcher.

The creator path of the walker creates the list of dicts and then the applier
path updates the dict that the creator generates in place.

The converters of the walker describe how to convert each of the supported
Attrs into a ValueAttr containing the query params corresponding to that part
of the query.
"""


@walker.add_creator(AttrOr)
def create_from_or(wlk, tree):
    """
    For each subtree under the OR, create a new set of query params.
    """
    params = []
    for sub in tree.attrs:
        params.append(wlk.create(sub))

    return params


@walker.add_creator(AttrAnd, ValueAttr)
def create_new_param(wlk, tree):
    params = dict()

    # Use the apply dispatcher to convert the attrs to their query parameters
    wlk.apply(tree, params)

    return [params]


@walker.add_applier(AttrAnd)
def iterate_over_and(wlk, tree, params):
    for sub in tree.attrs:
        wlk.apply(sub, params)


@walker.add_applier(ValueAttr)
def add_value_to_params(wlk, attr, params):
    # Modify params in place by combining it with the dict contained in the
    # ValueAttr
    params.update(attr.attrs)


# SunPy Attrs

@walker.add_converter(Time)
def _(attr):
    return ValueAttr({'': ''})


@walker.add_converter(Instrument)
def _(attr):
    return ValueAttr({'': ''})


@walker.add_converter(Wavelength)
def _(attr):
    return ValueAttr({'': ''})


@walker.add_converter(Physobs)
def _(attr):
    return ValueAttr({'': ''})


# DKIST Attrs


@walker.add_converter(Dataset)
def _(attr):
    return ValueAttr({'': ''})


@walker.add_converter(WavelengthBand)
def _(attr):
    return ValueAttr({'': ''})


@walker.add_converter(Observable)
def _(attr):
    return ValueAttr({'': ''})


@walker.add_converter(Experiment)
def _(attr):
    return ValueAttr({'': ''})


@walker.add_converter(Proposal)
def _(attr):
    return ValueAttr({'': ''})


@walker.add_converter(TargetType)
def _(attr):
    return ValueAttr({'': ''})


@walker.add_converter(Recipe)
def _(attr):
    return ValueAttr({'': ''})


@walker.add_converter(RecipeInstance)
def _(attr):
    return ValueAttr({'': ''})


@walker.add_converter(Embargoed)
def _(attr):
    return ValueAttr({'': ''})


@walker.add_converter(FriedParameter)
def _(attr):
    return ValueAttr({'': ''})


@walker.add_converter(PolarimetricAccuracy)
def _(attr):
    return ValueAttr({'': ''})


@walker.add_converter(ExposureTime)
def _(attr):
    return ValueAttr({'': ''})


@walker.add_converter(CreationTime)
def _(attr):
    return ValueAttr({'': ''})


@walker.add_converter(EmbargoEndTime)
def _(attr):
    return ValueAttr({'': ''})


@walker.add_converter(BrowseMovie)
def _(attr):
    return ValueAttr({'': ''})


@walker.add_converter(BoundingBox)
def _(attr):
    return ValueAttr({'': ''})
