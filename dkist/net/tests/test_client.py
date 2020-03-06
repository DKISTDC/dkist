import json

import hypothesis.strategies as st  # noqa
import pytest
from hypothesis import given

from sunpy.net import Fido, attr
from sunpy.net import attrs as a
from sunpy.tests.helpers import no_vso

from dkist.net.client import DKISTDatasetClient, DKISTQueryReponse
from dkist.net.tests import strategies as dst  # noqa


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


@pytest.fixture
def mocked_client(mocker, client, example_api_response):
    """
    Return a client instance with any external service calls mocked.
    """
    urlopen = mocker.patch("urllib.request.urlopen")
    open_mock = mocker.Mock()
    open_mock.read.return_value = json.dumps(example_api_response)
    urlopen.return_value = open_mock
    return client


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


@given(dst.query_and())
def test_apply_and(s):
    assert isinstance(s, (attr.AttrAnd, attr.DataAttr))


@given(dst.query_or())
def test_apply_or(s):
    assert isinstance(s, (attr.AttrOr, attr.DataAttr))


@given(dst.query_or_composite())
def test_apply_or_and(s):
    assert isinstance(s, (attr.AttrOr, attr.DataAttr, attr.AttrAnd))


@given(dst.query_and())
def test_search_query_and(mocked_client, query):
    res = mocked_client.search(query)
    assert isinstance(res, DKISTQueryReponse)
    assert len(res) == 1


@given(dst.query_or_composite())
def test_search_query_or(mocked_client, query):
    res = mocked_client.search(query)
    assert isinstance(res, DKISTQueryReponse)
    assert len(res) == 1


@given(dst.query_and())
def test_can_handle_query(client, query):
    # Can handle query never gets passed an AttrOr
    # It also never passes an AttrAnd, just the components of it
    if isinstance(query, attr.AttrAnd):
        assert client._can_handle_query(*query.attrs)
    else:
        assert client._can_handle_query(query)


@pytest.mark.parametrize("query", (
    a.Instrument("bob"),
    a.Physobs("who's got the button"),
    a.Level(2),
    (a.Instrument("VBI"), a.Level(0)),
    (a.Instrument("VBI"), a.Detector("test")),
    tuple(),
))
def test_cant_handle_query(client, query):
    """Some examples of invalid queries."""
    assert not client._can_handle_query(query)


@no_vso
@given(st.one_of(dst.query_and(), dst.query_or(), dst.query_or_composite()))
def test_fido_valid(mocker, mocked_client, query):
    # Test that Fido is passing through our queries to our client
    mocked_search = mocker.patch('dkist.net.client.DKISTDatasetClient.search')
    mocked_search.return_value = DKISTQueryReponse()

    Fido.search(query)
    assert mocked_search.called

    if isinstance(query, (attr.DataAttr, attr.AttrAnd)):
        assert mocked_search.call_count == 1

    if isinstance(query, attr.AttrOr):
        assert mocked_search.call_count == len(query.attrs)
