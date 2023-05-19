import json
import pathlib

import globus_sdk
import pytest

import dkist.net
from dkist.data.test import rootdir
from dkist.net.globus.endpoints import (get_data_center_endpoint_id, get_directory_listing,
                                        get_endpoint_id, get_local_endpoint_id,
                                        get_transfer_client)


@pytest.fixture
def endpoint_search(mocker, transfer_client):
    with open(rootdir / "globus_search_response.json") as fd:
        data = json.load(fd)

    responses = []
    for d in data:
        response = mocker.MagicMock()
        response.json = lambda: d
        responses.append(globus_sdk.response.GlobusHTTPResponse(response, transfer_client))
    return {"DATA": responses}


@pytest.fixture
def ls_response(mocker, transfer_client):
    with open(rootdir / "globus_operation_ls_response.json") as fd:
        data = json.load(fd)

    resp = globus_sdk.services.transfer.response.iterable.IterableTransferResponse(mocker.MagicMock(), client=transfer_client)
    mocker.patch("globus_sdk.services.transfer.response.iterable.IterableTransferResponse.data",
                 new_callable=mocker.PropertyMock(return_value=data))

    return resp


@pytest.fixture
def mock_search(mocker):
    mocker.patch("globus_sdk.TransferClient.endpoint_search",
                 return_value=globus_sdk.services.transfer.response.iterable.IterableTransferResponse)
    return mocker.patch("globus_sdk.services.transfer.response.iterable.IterableTransferResponse.data",
                        new_callable=mocker.PropertyMock)


def test_get_transfer_client(mocker, transfer_client):
    assert isinstance(transfer_client, globus_sdk.TransferClient)


@pytest.mark.parametrize("endpoint_id", ("12345", None))
def test_get_local_endpoint_id(mocker, endpoint_id):
    lgcp_mock = mocker.patch("globus_sdk.LocalGlobusConnectPersonal.endpoint_id",
                             new_callable=mocker.PropertyMock)
    lgcp_mock.return_value = endpoint_id

    if endpoint_id is None:
        with pytest.raises(ConnectionError):
            get_local_endpoint_id()
    else:
        a = get_local_endpoint_id()
        assert a is endpoint_id


def test_get_endpoint_id_search(mocker, mock_search, endpoint_search, transfer_client):
    mock_search.return_value = endpoint_search

    transfer_client = get_transfer_client()

    # Test exact display name match
    endpoint_id = get_endpoint_id('NCAR Data Sharing Service', transfer_client)
    assert endpoint_id == "dd1ee92a-6d04-11e5-ba46-22000b92c6ec"

    # Test multiple match fail
    with pytest.raises(ValueError) as exc:
        get_endpoint_id(" ", transfer_client)
    assert "Multiple" in str(exc.value)

    # Test just one result
    mock_search.return_value = {"DATA": endpoint_search["DATA"][1:2]}
    endpoint_id = get_endpoint_id(" ", transfer_client)
    assert endpoint_id == "dd1ee92a-6d04-11e5-ba46-22000b92c6ec"

    # Test no results
    mock_search.return_value = {"DATA": []}
    with pytest.raises(ValueError) as e_info:
        get_endpoint_id(" ", transfer_client)
    assert "No matches" in str(e_info.value)


def test_get_endpoint_id_uuid(mocker, transfer_client, endpoint_search):
    mocker.patch.object(transfer_client, "get_endpoint",
                        mocker.Mock(return_value=globus_sdk.services.transfer.response.iterable.IterableTransferResponse))
    get_ep_mock = mocker.patch("globus_sdk.services.transfer.response.iterable.IterableTransferResponse.data",
                               new_callable=mocker.PropertyMock)
    get_ep_mock.return_value = {"DATA": endpoint_search["DATA"][1:2]}

    endpoint_id = get_endpoint_id('dd1ee92a-6d04-11e5-ba46-22000b92c6ec', transfer_client)
    assert endpoint_id == "dd1ee92a-6d04-11e5-ba46-22000b92c6ec"


def test_get_endpoint_id_invalid_uuid(mocker, mock_search, transfer_client, endpoint_search):
    err = globus_sdk.TransferAPIError(mocker.MagicMock())
    mocker.patch("globus_sdk.TransferClient.get_endpoint",
                 side_effect=err)
    mock_search.return_value = {"DATA": endpoint_search["DATA"][1:2]}

    # Test Other transfer error
    with pytest.raises(globus_sdk.TransferAPIError):
        get_endpoint_id("wibble", transfer_client)

    # Test EndpointNotFound error
    mocker.patch.object(err, "code", "EndpointNotFound")
    endpoint_id = get_endpoint_id("wibble", transfer_client)
    assert endpoint_id == "dd1ee92a-6d04-11e5-ba46-22000b92c6ec"


def test_directory_listing(mocker, transfer_client, ls_response):
    mocker.patch("dkist.net.globus.endpoints.auto_activate_endpoint")
    mocker.patch("dkist.net.globus.endpoints.get_endpoint_id", return_value="12345")
    mocker.patch("dkist.net.globus.endpoints.get_local_endpoint_id",
                 return_value="12345")
    mocker.patch("globus_sdk.TransferClient.operation_ls",
                 return_value=ls_response)

    ls = get_directory_listing("/")
    assert all([isinstance(a, pathlib.Path) for a in ls])
    assert len(ls) == 13

    ls = get_directory_listing("/", "1234")
    assert all([isinstance(a, pathlib.Path) for a in ls])
    assert len(ls) == 13


def test_get_datacenter_endpoint_id(httpserver):
    httpserver.expect_request("/datasets/v1/config",).respond_with_data(
        json.dumps({"globusDataEndpointID": "example_endpoint_id"}),
    )

    with dkist.net.conf.set_temp("dataset_endpoint",
                                 httpserver.url_for("/datasets/")):
        endpoint_id = get_data_center_endpoint_id()

    assert endpoint_id == "example_endpoint_id"
