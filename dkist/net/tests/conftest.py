import pytest

from sunpy.net import attrs as a

import dkist.net.attrs as da


@pytest.fixture(scope="session")
def httpserver_listen_address():
    return ("127.0.0.1", 8888)

@pytest.fixture(params=da.__all__)
def all_dkist_attrs_classes(request):
    return getattr(da, request.param)


@pytest.fixture(params=da.__all__ + ['Time', 'Instrument', 'Wavelength', 'Physobs'])
def all_attrs_classes(request):
    at = getattr(da, request.param, None)
    return at or getattr(a, request.param)


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
        a.Provider: tuple(),
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
        da.SpectralSampling: ('averageDatasetSpectralSamplingMin', 'averageDatasetSpectralSamplingMax'),
        da.SpatialSampling: ('averageDatasetSpatialSamplingMin', 'averageDatasetSpatialSamplingMax'),
        da.TemporalSampling: ('averageDatasetTemporalSamplingMin', 'averageDatasetTemporalSamplingMax'),
    }
