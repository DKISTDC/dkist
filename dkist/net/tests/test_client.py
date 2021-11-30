import json

import hypothesis.strategies as st  # noqa
import parfive
import pytest
from hypothesis import HealthCheck, given, settings

from sunpy.net import Fido, attr
from sunpy.net import attrs as a
from sunpy.net.base_client import QueryResponseRow
from sunpy.tests.helpers import no_vso

from dkist.net.client import DKISTDatasetClient, DKISTQueryResponseTable
from dkist.net.tests import strategies as dst  # noqa


@pytest.fixture
def client():
    return DKISTDatasetClient()


@pytest.mark.skip
@pytest.mark.remote_data
def test_search(client):
    # TODO: Write an online test to verify real behaviour once there is stable data
    res = client.search(a.Time("2019/01/01", "2021/01/01"))


@pytest.fixture
def empty_query_response():
    return DKISTQueryResponseTable()


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
                "targetTypes": ["string"],
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
def expected_table_keys():
    translated_keys = set(DKISTQueryResponseTable.key_map.values())
    removed_keys = {'Wavelength Min', 'Wavelength Max'}
    added_keys = {'Wavelength'}
    expected_keys = translated_keys - removed_keys
    expected_keys.update(added_keys)
    return expected_keys


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


def test_query_response_from_results(empty_query_response, example_api_response, expected_table_keys):
    dclient = DKISTDatasetClient()
    qr = DKISTQueryResponseTable.from_results(example_api_response["searchResults"], client=dclient)

    assert len(qr) == 1
    assert isinstance(qr.client, DKISTDatasetClient)
    assert qr.client is dclient
    assert isinstance(qr[0], QueryResponseRow)
    assert not set(qr.colnames).difference(expected_table_keys)
    assert set(qr.colnames).isdisjoint(DKISTQueryResponseTable.key_map.keys())


def test_query_response_from_results_unknown_field(empty_query_response, example_api_response, expected_table_keys):
    """
    This test asserts that if the API starts returning new fields we don't error, they get passed though verbatim.
    """
    dclient = DKISTDatasetClient()
    resp = example_api_response["searchResults"]
    resp[0].update({'spamEggs': 'Some Spam'})
    qr = DKISTQueryResponseTable.from_results(resp, client=dclient)

    assert len(qr) == 1
    assert isinstance(qr.client, DKISTDatasetClient)
    assert qr.client is dclient
    assert isinstance(qr[0], QueryResponseRow)
    assert set(qr.colnames).difference(expected_table_keys) == {'spamEggs'}
    assert set(qr.colnames).isdisjoint(DKISTQueryResponseTable.key_map.keys())


def test_length_0_qr(empty_query_response):
    assert len(empty_query_response) == 0
    assert str(empty_query_response)
    assert repr(empty_query_response)
    assert empty_query_response._repr_html_()


@settings(suppress_health_check=[HealthCheck.too_slow])
@given(dst.query_and())
def test_apply_and(s):
    assert isinstance(s, (attr.AttrAnd, attr.DataAttr))


@settings(suppress_health_check=[HealthCheck.too_slow])
@given(dst.query_or())
def test_apply_or(s):
    assert isinstance(s, (attr.AttrOr, attr.DataAttr))


@settings(suppress_health_check=[HealthCheck.too_slow])
@given(dst.query_or_composite())
def test_apply_or_and(s):
    assert isinstance(s, (attr.AttrOr, attr.DataAttr, attr.AttrAnd))


@settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
          deadline=None)
@given(dst.query_and())
def test_search_query_and(mocked_client, query):
    res = mocked_client.search(query)
    assert isinstance(res, DKISTQueryResponseTable)
    assert len(res) == 1


@settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
          deadline=None)
@given(dst.query_or_composite())
def test_search_query_or(mocked_client, query):
    res = mocked_client.search(query)
    assert isinstance(res, DKISTQueryResponseTable)
    if isinstance(query, attr.AttrOr):
        assert len(res) == len(query.attrs)
    else:
        assert len(res) == 1


@settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
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
@settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture], deadline=None)
@given(st.one_of(dst.query_and(), dst.query_or(), dst.query_or_composite()))
def test_fido_valid(mocker, mocked_client, query):
    # Test that Fido is passing through our queries to our client
    mocked_search = mocker.patch('dkist.net.client.DKISTDatasetClient.search')
    mocked_search.return_value = DKISTQueryResponseTable()

    Fido.search(query)
    assert mocked_search.called

    if isinstance(query, (attr.DataAttr, attr.AttrAnd)):
        assert mocked_search.call_count == 1

    if isinstance(query, attr.AttrOr):
        assert mocked_search.call_count == len(query.attrs)


def test_fetch_with_headers(httpserver, tmpdir, mocked_client):
    httpserver.expect_request("/download/asdf",
                              query_string="datasetId=abcd").respond_with_data(
                                  b"This isn't an asdf",
                                  headers={"Content-Disposition": "attachment; filename=abcd.asdf"}
                              )

    mocked_client._BASE_DOWNLOAD_URL = httpserver.url_for("/download")

    response = DKISTQueryResponseTable({'Dataset ID': ['abcd']})

    downloader = parfive.Downloader()
    mocked_client.fetch(response, downloader=downloader, path=tmpdir)

    assert len(downloader.http_queue) == 1

    results = downloader.download()
    assert len(results) == 1, results.errors

    assert results[0] == str(tmpdir / "abcd.asdf")
