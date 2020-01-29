import astropy.units as u
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
        sub_params = wlk.create(sub)

        # Strip out one layer of nesting of lists
        # This means that create always returns a list of dicts.
        if isinstance(sub_params, list) and len(sub_params) == 1:
            sub_params = sub_params[0]

        params.append(sub_params)

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


# Converters from Attrs to ValueAttrs
# SunPy Attrs

@walker.add_converter(Time)
def _(attr):
    return ValueAttr({'startTimeMin': attr.start.isot,
                      'endTimeMax': attr.end.isot})


@walker.add_converter(Instrument)
def _(attr):
    return ValueAttr({'instrumentNames': [attr.value]})


@walker.add_converter(Wavelength)
def _(attr):
    return ValueAttr({'wavelengthMinMin': attr.min.to_value(u.nm),
                      'wavelengthMaxMax': attr.max.to_value(u.nm)})


@walker.add_converter(Physobs)
def _(attr):
    if attr.value == "stokes_parameters":
        return ValueAttr({'hasAllStokes': True})
    if attr.value == "intensity":
        return ValueAttr({'hasAllStokes': False})

    # The client should not have accepted the query if we make it this far.
    raise ValueError(f"Physobs({attr.value}) is not supported by the DKIST client.")


# DKIST Attrs


@walker.add_converter(Dataset)
def _(attr):
    return ValueAttr({'datasetIds': [attr.value]})


@walker.add_converter(WavelengthBand)
def _(attr):
    return ValueAttr({'filterWavelengths': [attr.value]})


@walker.add_converter(Observable)
def _(attr):
    return ValueAttr({'observables': [attr.value]})


@walker.add_converter(Experiment)
def _(attr):
    return ValueAttr({'primaryExperimentIds': [attr.value]})


@walker.add_converter(Proposal)
def _(attr):
    return ValueAttr({'primaryProposalIds': [attr.value]})


@walker.add_converter(TargetType)
def _(attr):
    return ValueAttr({'targetTypes': [attr.value]})


@walker.add_converter(Recipe)
def _(attr):
    return ValueAttr({'recipeId': int(attr.value)})


@walker.add_converter(RecipeInstance)
def _(attr):
    return ValueAttr({'recipeInstanceId': int(attr.value)})


@walker.add_converter(Embargoed)
def _(attr):
    return ValueAttr({'isEmbargoed': bool(attr.value)})


@walker.add_converter(FriedParameter)
def _(attr):
    return ValueAttr({'qualityAverageFriedParameterMin': attr.min,
                      'qualityAverageFriedParameterMax': attr.max})


@walker.add_converter(PolarimetricAccuracy)
def _(attr):
    return ValueAttr({'qualityAveragePolarimetricAccuracyMin': attr.min,
                      'qualityAveragePolarimetricAccuracyMax': attr.max})


@walker.add_converter(ExposureTime)
def _(attr):
    return ValueAttr({'exposureTimeMin': attr.min.to_value(u.s),
                      'exposureTimeMax': attr.max.to_value(u.s)})


@walker.add_converter(CreationTime)
def _(attr):
    return ValueAttr({'createDateMin': attr.start.isot,
                      'createDateMax': attr.end.isot})


@walker.add_converter(EmbargoEndTime)
def _(attr):
    return ValueAttr({'embargoEndDateMin': attr.start.isot,
                      'embargoEndDateMax': attr.end.isot})


@walker.add_converter(BrowseMovie)
def _(attr):
    values = {}
    if attr.movieurl:
        values['browseMovieUrl'] = attr.movieurl
    if attr.movieobjectkey:
        values['browseMovieObjectKey'] = attr.movieobjectkey

    return ValueAttr(values)


@walker.add_converter(BoundingBox)
def _(attr):
    raise NotImplementedError("Support for bounding box isn't implemented")
    return ValueAttr({'': ''})
