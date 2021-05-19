import astropy.units as u
from sunpy.net.attr import AttrAnd, AttrOr, AttrWalker, DataAttr
from sunpy.net.attrs import Instrument, Level, Physobs, Provider, Time, Wavelength

from .attrs import *

walker = AttrWalker()
"""
The DKIST Client walker works by the creator creating a list of dicts, which
become the query parameters to the call to the dataset searcher.

The creator path of the walker creates the list of dicts and then the applier
path updates the dict by converting the attrs to their query parameters.
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


@walker.add_creator(AttrAnd, DataAttr)
def create_new_param(wlk, tree):
    params = dict()

    # Use the apply dispatcher to convert the attrs to their query parameters
    wlk.apply(tree, params)

    return [params]


@walker.add_applier(AttrAnd)
def iterate_over_and(wlk, tree, params):
    for sub in tree.attrs:
        wlk.apply(sub, params)


# Converters from Attrs to ValueAttrs
# SunPy Attrs
@walker.add_applier(Time)
def _(wlk, attr, params):
    return params.update({'startTimeMin': attr.start.isot,
                          'endTimeMax': attr.end.isot})


@walker.add_applier(Instrument)
def _(wlk, attr, params):
    return params.update({'instrumentNames': attr.value})


@walker.add_applier(Wavelength)
def _(wlk, attr, params):
    return params.update({'wavelengthMinMin': attr.min.to_value(u.nm),
                          'wavelengthMaxMax': attr.max.to_value(u.nm)})


@walker.add_applier(Physobs)
def _(wlk, attr, params):
    if attr.value.lower() == "stokes_parameters":
        return params.update({'hasAllStokes': True})
    if attr.value.lower() == "intensity":
        return params.update({'hasAllStokes': False})
    if attr.value.lower() == "spectral_axis":
        return params.update({'hasSpectralAxis': True})
    if attr.value.lower() == "temporal_axis":
        return params.update({'hasTemporalAxis': True})

    # The client should not have accepted the query if we make it this far.
    raise ValueError(f"Physobs({attr.value}) is not supported by the DKIST client.")  # pragma: no cover


# DKIST Attrs
@walker.add_applier(Dataset)
def _(wlk, attr, params):
    return params.update({'datasetIds': attr.value})


@walker.add_applier(WavelengthBand)
def _(wlk, attr, params):
    return params.update({'filterWavelengths': attr.value})


@walker.add_applier(Observable)
def _(wlk, attr, params):
    return params.update({'observables': attr.value})


@walker.add_applier(Experiment)
def _(wlk, attr, params):
    return params.update({'primaryExperimentIds': attr.value})


@walker.add_applier(Proposal)
def _(wlk, attr, params):
    return params.update({'primaryProposalIds': attr.value})


@walker.add_applier(TargetType)
def _(wlk, attr, params):
    return params.update({'targetTypes': attr.value})


@walker.add_applier(Recipe)
def _(wlk, attr, params):
    return params.update({'recipeId': attr.value})


@walker.add_applier(Embargoed)
def _(wlk, attr, params):
    return params.update({'isEmbargoed': bool(attr.value)})


@walker.add_applier(FriedParameter)
def _(wlk, attr, params):
    return params.update({'qualityAverageFriedParameterMin': attr.min,
                          'qualityAverageFriedParameterMax': attr.max})


@walker.add_applier(PolarimetricAccuracy)
def _(wlk, attr, params):
    return params.update({'qualityAveragePolarimetricAccuracyMin': attr.min,
                          'qualityAveragePolarimetricAccuracyMax': attr.max})


@walker.add_applier(ExposureTime)
def _(wlk, attr, params):
    return params.update({'exposureTimeMin': attr.min.to_value(u.s),
                          'exposureTimeMax': attr.max.to_value(u.s)})


@walker.add_applier(EmbargoEndTime)
def _(wlk, attr, params):
    return params.update({'embargoEndDateMin': attr.start.isot,
                          'embargoEndDateMax': attr.end.isot})

@walker.add_applier(SpectralSampling)
def _(wlk, attr, params):
    return params.update({'averageDatasetSpectralSamplingMin': attr.min.to_value(equivalencies=float),
                          'averageDatasetSpectralSamplingMax': attr.max.to_value(equivalencies=float)})

@walker.add_applier(SpatialSampling)
def _(wlk, attr, params):
    return params.update({'averageDatasetSpatialSamplingMin': attr.min.to_value(equivalencies=float),
                          'averageDatasetSpatialSamplingMax': attr.max.to_value(equivalencies=float)})

@walker.add_applier(TemporalSampling)
def _(wlk, attr, params):
    return params.update({'averageDatasetTemporalSamplingMin': attr.min.to_value(u.s),
                          'averageDatasetTemporalSamplingMax': attr.max.to_value(u.s)})

@walker.add_applier(BrowseMovie)
def _(wlk, attr, params):
    values = {}
    if attr.movieurl:
        values['browseMovieUrl'] = attr.movieurl
    if attr.movieobjectkey:
        values['browseMovieObjectKey'] = attr.movieobjectkey

    return params.update(values)


@walker.add_applier(BoundingBox)
def _(wlk, attr, params):
    search_types = {"containing": "rectangleContainingBoundingBox",
                    "contained": "rectangleContainedByBoundingBox",
                    "intersecting": "rectangleIntersectingBoundingBox"}

    # strip all spaces and the outer most ()
    return params.update({search_types[attr.search_type]: str(attr.hpc_bounding_box_arcsec).replace(' ', '')[1:-1]})


@walker.add_applier(Provider)
def _(wlk, attr, params):
    """
    Provider is used by client _can_handle_query and not the API.
    """

@walker.add_applier(Level)
def _(wlk, attr, params):
    """
    Level is used by client _can_handle_query and not the API.
    """
