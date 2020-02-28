import pytest

from sunpy.net import attrs as a

import dkist.net.attrs as da  # noqa
from dkist.net.client import DKISTDatasetClient, DKISTQueryReponse


@pytest.fixture
def client():
    return DKISTDatasetClient()


@pytest.mark.remote_data
@pytest.mark.skip
def test_search(client):
    res = client.search(a.Time("2019/01/01", "2021/01/01"))
    print(res)


@pytest.fixture
def empty_query_response():
    return DKISTQueryReponse()


@pytest.fixture
def example_api_response():
    return {
        "authorizationStatusCode": "string",
        "authorizationStatusDescription": "string",
        "searchResults": [
            {
                "asdfObjectKey": "string",
                "boundingBox": "string",
                "browseMovieObjectKey": "string",
                "bucket": "string",
                "datasetId": "string",
                "datasetSize": 0,
                "endTime": "2020-02-28T17:05:53.330Z",
                "contributingExperimentIds": ["string"],
                "exposureTime": 0,
                "filterWavelengths": [0],
                "frameCount": 0,
                "instrumentName": "string",
                "observables": ["string"],
                "originalFrameCount": 0,
                "primaryExperimentId": "string",
                "primaryProposalId": "string",
                "contributingProposalIds": ["string"],
                "qualityAverageFriedParameter": 0,
                "qualityAveragePolarimetricAccuracy": 0,
                "recipeInstanceId": 0,
                "recipeRunId": 0,
                "recipeId": 0,
                "startTime": "2020-02-28T17:05:53.330Z",
                "hasAllStokes": True,
                "stokesParameters": "string",
                "targetType": "string",
                "wavelengthMax": 0,
                "wavelengthMin": 0,
                "createDate": "2020-02-28T17:05:53.330Z",
                "experimentDescription": "string",
                "isEmbargoed": True,
                "updateDate": "2020-02-28T17:05:53.330Z",
                "embargoEndDate": "2020-02-28T17:05:53.330Z",
                "browseMovieUrl": "string",
                "isDownloadable": True,
            }
        ],
    }


def test_append_query_response(empty_query_response, example_api_response):
    qr = empty_query_response
    qr._append_results(example_api_response["searchResults"])

    assert len(qr) == 1
    assert isinstance(qr.client, DKISTDatasetClient)
    dclient = DKISTDatasetClient()
    qr.client = dclient
    assert qr.client is dclient
    assert qr.build_table() is qr.table
    assert len(qr.table) == len(qr)
    assert isinstance(qr[0], DKISTQueryReponse)
    assert not set(qr.table.columns).difference(DKISTQueryReponse.key_map.values())
    assert set(qr.table.columns).isdisjoint(DKISTQueryReponse.key_map.keys())
    assert all(x in str(qr) for x in DKISTQueryReponse._core_keys)
    assert all(x in qr._repr_html_() for x in DKISTQueryReponse._core_keys)
    assert isinstance(qr.blocks, list)
    assert qr.blocks == list(qr.table.iterrows())

    assert DKISTQueryReponse.from_results(example_api_response["searchResults"]) == qr


def test_length_0_qr(empty_query_response):
    assert len(empty_query_response) == 0
    assert str(empty_query_response)
    assert repr(empty_query_response)
    assert empty_query_response._repr_html_()
