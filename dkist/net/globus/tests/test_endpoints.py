import json
import pathlib

import globus_sdk
import pytest

from dkist.data.test import rootdir
from dkist.net.globus.endpoints import (get_directory_listing, get_endpoint_id,
                                        get_local_endpoint_id, get_transfer_client)


@pytest.fixture
def endpoint_search():
    with open(rootdir / "globus_search_response.json") as fd:
        data = json.load(fd)

    data = [globus_sdk.response.GlobusResponse(d) for d in data][1:]
    return data


@pytest.fixture
def ls_response(mocker):
    with open(rootdir / "globus_operation_ls_response.json") as fd:
        data = json.load(fd)

    resp = globus_sdk.transfer.response.IterableTransferResponse(mocker.MagicMock())
    mocker.patch("globus_sdk.transfer.response.IterableTransferResponse.data",
                 new_callable=mocker.PropertyMock(return_value=data))

    return resp


@pytest.fixture
def mock_search(mocker):
    mocker.patch("globus_sdk.TransferClient.endpoint_search",
                 return_value=globus_sdk.transfer.paging.PaginatedResource)
    return mocker.patch("globus_sdk.transfer.paging.PaginatedResource.data",
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
    mock_search.return_value = endpoint_search[0:1]
    endpoint_id = get_endpoint_id(" ", transfer_client)
    assert endpoint_id == "dd1ee92a-6d04-11e5-ba46-22000b92c6ec"

    # Test no results
    mock_search.return_value = []
    with pytest.raises(ValueError) as e_info:
        get_endpoint_id(" ", transfer_client)
    assert "No matches" in str(e_info.value)


def test_get_endpoint_id_uuid(mocker, transfer_client, endpoint_search):
    mocker.patch.object(transfer_client, "get_endpoint",
                        mocker.Mock(return_value=globus_sdk.transfer.paging.PaginatedResource))
    get_ep_mock = mocker.patch("globus_sdk.transfer.paging.PaginatedResource.data",
                               new_callable=mocker.PropertyMock)
    get_ep_mock.return_value = endpoint_search[0:1]

    endpoint_id = get_endpoint_id('dd1ee92a-6d04-11e5-ba46-22000b92c6ec', transfer_client)
    assert endpoint_id == "dd1ee92a-6d04-11e5-ba46-22000b92c6ec"


def test_get_endpoint_id_invalid_uuid(mocker, mock_search, transfer_client, endpoint_search):
    err = globus_sdk.TransferAPIError(mocker.MagicMock())
    mocker.patch("globus_sdk.TransferClient.get_endpoint",
                 side_effect=err)
    mock_search.return_value = endpoint_search[0:1]

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
