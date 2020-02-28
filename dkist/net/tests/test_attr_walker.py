import pytest

import astropy.units as u
from sunpy.net import attr
from sunpy.net import attrs as a

import dkist.net.attrs as da
from dkist.net.attr_walker import walker


@pytest.fixture
def api_param_names():
    """
    A mapping of attrs to param names in the query string.

    Excludes ones with input dependant query params
    """
    return {
        a.Time: ('startTimeMin', 'endTimeMax'),
        a.Instrument: ('instrumentNames',),
        a.Wavelength: ('wavelengthMinMin', 'wavelengthMaxMax'),
        a.Physobs: ('hasAllStokes',),
        da.Dataset: ('datasetIds',),
        da.WavelengthBand: ('filterWavelengths',),
        da.Observable: ('observables',),
        da.Experiment: ('primaryExperimentIds',),
        da.Proposal: ('primaryProposalIds',),
        da.TargetType: ('targetTypes',),
        da.Recipe: ('recipeId',),
        da.Embargoed: ('isEmbargoed',),
        da.FriedParameter: ('qualityAverageFriedParameterMin', 'qualityAverageFriedParameterMax'),
        da.PolarimetricAccuracy: ('qualityAveragePolarimetricAccuracyMin', 'qualityAveragePolarimetricAccuracyMax'),
        da.ExposureTime: ('exposureTimeMin', 'exposureTimeMax'),
        da.EmbargoEndTime: ('embargoEndDateMin', 'embargoEndDateMax'),
        da.Provider: tuple(),
        }


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
def all_dkist_attrs_classes(request):
    return getattr(da, request.param)


@pytest.fixture(params=da.__all__ + ['Time', 'Instrument', 'Wavelength', 'Physobs'])
def all_attrs_classes(request):
    at = getattr(da, request.param, None)
    return at or getattr(a, request.param)


def test_walker_single(all_attrs_classes, api_param_names):
    at = None

    if issubclass(all_attrs_classes, attr.SimpleAttr):
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

    if not at:
        pytest.skip(f"Not testing {all_attrs_classes!r}")

    params = walker.create(at)
    assert isinstance(params, list)
    assert len(params) == 1
    assert isinstance(params[0], dict)
    assert len(params[0]) == len(api_param_names[all_attrs_classes])
    assert not set(api_param_names[all_attrs_classes]).difference(params[0].keys())


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
