from pathlib import Path
from unittest import mock
from collections import namedtuple

import pytest
from globus_sdk import GlobusHTTPResponse
from globus_sdk.services.transfer.response.iterable import IterableTransferResponse

from dkist.net.globus.transfer import (_get_speed, _orchestrate_transfer_task,
                                       _process_task_events, start_transfer_from_file_list)


@pytest.fixture
def mock_endpoints(mocker):
    def id_mock(endpoint, tfr_client):
        return endpoint
    mocker.patch("dkist.net.globus.transfer.auto_activate_endpoint")
    return mocker.patch("dkist.net.globus.transfer.get_endpoint_id",
                        side_effect=id_mock)


def json_to_response(json):
    response = mock.MagicMock()
    response.json = lambda: json
    return response


@pytest.fixture
def mock_task_event_list(mocker, transfer_client):
    mock_response = GlobusHTTPResponse(
        json_to_response(
            {
                "DATA": [
                    {
                        "DATA_TYPE": "event",
                        "code": "STARTED",
                        "description": "started",
                        "details":
                        '{\n  "type": "GridFTP Transfer", \n  "concurrency": 2, \n  "protocol": "Mode S"\n}',
                        "is_error": False,
                        "parent_task_id": None,
                        "time": "2019-05-16 10:13:26+00:00"},
                    {
                        "DATA_TYPE": "event",
                        "code": "SUCCEEDED",
                        "description": "succeeded",
                        "details": "Scanned 100 file(s)",
                        "is_error": False,
                        "parent_task_id": None,
                        "time": "2019-05-16 10:13:24+00:00"},
                    {
                        "DATA_TYPE": "event",
                        "code": "STARTED",
                        "description": "started",
                        "details": "Starting sync scan",
                        "is_error": False,
                        "parent_task_id": None,
                        "time": "2019-05-16 10:13:20+00:00"},
                ],
                "DATA_TYPE": "event_list",
                "limit": 10,
                "offset": 0,
                "total": 3
            }
        ),
        client=True  # Not a client object
    )
    task_list = IterableTransferResponse(mock_response)
    return mocker.patch("globus_sdk.TransferClient.task_event_list",
                        return_value=task_list)


def test_start_transfer(mocker, transfer_client, mock_endpoints):
    submit_mock = mocker.patch("globus_sdk.TransferClient.submit_transfer",
                               return_value={"task_id": "task_id"})
    mocker.patch("globus_sdk.TransferClient.get_submission_id",
                 return_value={"value": "wibble"})
    file_list = list(map(Path, ["/a/name.fits", "/a/name2.fits"]))
    start_transfer_from_file_list("a", "b", "/", file_list)
    calls = mock_endpoints.call_args_list
    assert calls[0][0][0] == "a"
    assert calls[1][0][0] == "b"

    submit_mock.assert_called_once()
    transfer_manifest = submit_mock.call_args_list[0][0][0]["DATA"]

    # NOTE: These paths should always be posix not platform specific
    for filepath, tfr in zip(file_list, transfer_manifest):
        assert filepath.as_posix() == tfr["source_path"]
        assert f"/{filepath.name}" == tfr["destination_path"]


def test_start_transfer_src_base(mocker, transfer_client, mock_endpoints):
    submit_mock = mocker.patch("globus_sdk.TransferClient.submit_transfer",
                               return_value={"task_id": "task_id"})
    file_list = list(map(Path, ["/a/b/name.fits", "/a/b/name2.fits"]))
    start_transfer_from_file_list("a", "b", "/", file_list, "/a")
    calls = mock_endpoints.call_args_list
    assert calls[0][0][0] == "a"
    assert calls[1][0][0] == "b"

    submit_mock.assert_called_once()
    transfer_manifest = submit_mock.call_args_list[0][0][0]["DATA"]

    # NOTE: These paths should always be posix not platform specific
    for filepath, tfr in zip(file_list, transfer_manifest):
        assert filepath.as_posix() == tfr["source_path"]
        assert f"/b/{filepath.name}" == tfr["destination_path"]


def test_start_transfer_multiple_paths(mocker, transfer_client, mock_endpoints):
    submit_mock = mocker.patch("globus_sdk.TransferClient.submit_transfer",
                               return_value={"task_id": "task_id"})
    mocker.patch("globus_sdk.TransferClient.get_submission_id",
                 return_value={"value": "wibble"})
    file_list = list(map(Path, ["/a/name.fits", "/a/name2.fits"]))
    dst_list = list(map(Path, ["/aplace/newname.fits", "/anotherplace/newname2.fits"]))
    start_transfer_from_file_list("a", "b", dst_list, file_list)
    transfer_manifest = submit_mock.call_args_list[0][0][0]["DATA"]

    for filepath, tfr in zip(dst_list, transfer_manifest):
        assert filepath.as_posix() == tfr["destination_path"]


def test_process_event_list(transfer_client, mock_task_event_list):
    (events,
     json_events,
     message_events) = _process_task_events("1234", set(), transfer_client)

    assert isinstance(events, set)
    assert all(isinstance(e, tuple) for e in events)
    assert all(all(isinstance(item, tuple) for item in e) for e in events)

    assert len(json_events) == 1
    assert isinstance(json_events, tuple)
    assert isinstance(json_events[0], dict)
    assert isinstance(json_events[0]["details"], dict)
    assert json_events[0]["code"] == "STARTED"

    assert len(message_events) == 2
    assert isinstance(message_events, tuple)
    assert isinstance(message_events[0], dict)
    assert isinstance(message_events[0]["details"], str)


def test_process_event_list_message_only(transfer_client, mock_task_event_list):
    # Filter out the json event
    prev_events = tuple(tuple(x.items()) for x in mock_task_event_list.return_value)
    prev_events = set(prev_events[0:1])

    (events,
     json_events,
     message_events) = _process_task_events("1234", prev_events, transfer_client)

    assert isinstance(events, set)
    assert all(isinstance(e, tuple) for e in events)
    assert all(all(isinstance(item, tuple) for item in e) for e in events)

    assert len(json_events) == 0
    assert isinstance(json_events, tuple)

    assert len(message_events) == 2
    assert isinstance(message_events, tuple)
    assert isinstance(message_events[0], dict)
    assert isinstance(message_events[0]["details"], str)


def test_get_speed():
    speed = _get_speed({"code": "PROGRESS", "details": {"mbps": 10}})
    assert speed == 10
    speed = _get_speed({})
    assert speed is None
    speed = _get_speed({"code": "progress", "details": "hello"})
    assert speed is None
    speed = _get_speed({"code": "progress", "details": {"hello": "world"}})
    assert speed is None


@pytest.fixture
def orchestrate_mocks(mocker):
    wtp = mocker.patch("dkist.net.globus.transfer.watch_transfer_progress",
                       autospec=True)
    mocker.patch("dkist.net.globus.transfer.get_local_endpoint_id",
                 autospec=True, return_value="mysecretendpoint")
    gtc = mocker.patch("dkist.net.globus.transfer.get_transfer_client",
                       autospec=True)
    mocker.patch("dkist.net.globus.transfer.get_data_center_endpoint_id",
                 return_value="patched-datacenter-endpoint-id",
                 autospec=True)
    start = mocker.patch("dkist.net.globus.transfer.start_transfer_from_file_list",
                         autospec=True, return_value="1234")
    mocks = namedtuple("mocks", "watch_transfer_progress get_transfer_client start_transfer_from_file_list")
    return mocks(wtp, gtc, start)


@pytest.fixture
def tfr_file_list():
    return ["file1.fits", "file2.fits"]


def test_orchestrate_transfer(tfr_file_list, orchestrate_mocks):
    _orchestrate_transfer_task(tfr_file_list, recursive=False,
                               destination_path=Path("/~/"))

    orchestrate_mocks.start_transfer_from_file_list.assert_called_once_with(
        "patched-datacenter-endpoint-id",
        "mysecretendpoint",
        Path("/~/"),
        tfr_file_list,
        recursive=False,
        label=None,
    )


def test_orchestrate_transfer_no_progress(tfr_file_list, mocker, orchestrate_mocks):
    _orchestrate_transfer_task(tfr_file_list, recursive=False,
                               destination_path=Path("/~/"),
                               progress=False)

    orchestrate_mocks.start_transfer_from_file_list.assert_called_once_with(
        "patched-datacenter-endpoint-id",
        "mysecretendpoint",
        Path("/~/"),
        tfr_file_list,
        recursive=False,
        label=None,
    )

    orchestrate_mocks.watch_transfer_progress.assert_not_called()
    orchestrate_mocks.get_transfer_client.return_value.task_wait.assert_called_once_with(
        "1234",
        timeout=1e6
    )


def test_orchestrate_transfer_no_wait(tfr_file_list, mocker, orchestrate_mocks):
    _orchestrate_transfer_task(tfr_file_list, recursive=False,
                               destination_path=Path("/~/"),
                               wait=False)

    orchestrate_mocks.start_transfer_from_file_list.assert_called_once_with(
        "patched-datacenter-endpoint-id",
        "mysecretendpoint",
        Path("/~/"),
        tfr_file_list,
        recursive=False,
        label=None,
    )

    orchestrate_mocks.watch_transfer_progress.assert_not_called()
    orchestrate_mocks.get_transfer_client.return_value.task_wait.assert_not_called()
