import os
import pathlib

import pytest
from globus_sdk import GlobusResponse

from dkist.net.globus.transfer import (_get_speed, _process_task_events,
                                       start_transfer_from_file_list)


@pytest.fixture
def mock_endpoints(mocker):
    def id_mock(endpoint, tc):
        return endpoint
    mocker.patch("dkist.net.globus.transfer.auto_activate_endpoint")
    return mocker.patch("dkist.net.globus.transfer.get_endpoint_id",
                        side_effect=id_mock)


@pytest.fixture
def mock_task_event_list(mocker):
    task_list = [
        GlobusResponse({
            'DATA_TYPE': 'event',
            'code': 'STARTED',
            'description': 'started',
            'details':
            '{\n  "type": "GridFTP Transfer", \n  "concurrency": 2, \n  "protocol": "Mode S"\n}',
            'is_error': False,
            'parent_task_id': None,
            'time': '2019-05-16 10:13:26+00:00'
        }),
        GlobusResponse({
            'DATA_TYPE': 'event',
            'code': 'SUCCEEDED',
            'description': 'succeeded',
            'details': 'Scanned 100 file(s)',
            'is_error': False,
            'parent_task_id': None,
            'time': '2019-05-16 10:13:24+00:00'
        }),
        GlobusResponse({
            'DATA_TYPE': 'event',
            'code': 'STARTED',
            'description': 'started',
            'details': 'Starting sync scan',
            'is_error': False,
            'parent_task_id': None,
            'time': '2019-05-16 10:13:20+00:00'
        })
    ]
    return mocker.patch("globus_sdk.TransferClient.task_event_list",
                        return_value=task_list)


def test_start_transfer(mocker, transfer_client, mock_endpoints):
    submit_mock = mocker.patch("globus_sdk.TransferClient.submit_transfer",
                               return_value={"task_id": "task_id"})
    mocker.patch("globus_sdk.TransferClient.get_submission_id",
                 return_value={'value': "wibble"})
    file_list = list(map(pathlib.Path, ["/a/name.fits", "/a/name2.fits"]))
    start_transfer_from_file_list("a", "b", "/", file_list)
    calls = mock_endpoints.call_args_list
    assert calls[0][0][0] == "a"
    assert calls[1][0][0] == "b"

    submit_mock.assert_called_once()
    transfer_manifest = submit_mock.call_args_list[0][0][0]['DATA']

    for filepath, tfr in zip(file_list, transfer_manifest):
        assert str(filepath) == tfr['source_path']
        assert os.path.sep + filepath.name == tfr['destination_path']


def test_start_transfer_src_base(mocker, transfer_client, mock_endpoints):
    submit_mock = mocker.patch("globus_sdk.TransferClient.submit_transfer",
                               return_value={"task_id": "task_id"})
    file_list = list(map(pathlib.Path, ["/a/b/name.fits", "/a/b/name2.fits"]))
    start_transfer_from_file_list("a", "b", "/", file_list, "/a")
    calls = mock_endpoints.call_args_list
    assert calls[0][0][0] == "a"
    assert calls[1][0][0] == "b"

    submit_mock.assert_called_once()
    transfer_manifest = submit_mock.call_args_list[0][0][0]['DATA']

    for filepath, tfr in zip(file_list, transfer_manifest):
        assert str(filepath) == tfr['source_path']
        assert "{0}b{0}".format(os.path.sep) + filepath.name == tfr['destination_path']


def test_process_event_list(transfer_client, mock_task_event_list):
    (events,
     json_events,
     message_events) = _process_task_events("1234", set(), transfer_client)

    assert isinstance(events, set)
    assert all([isinstance(e, tuple) for e in events])
    assert all([all([isinstance(item, tuple) for item in e]) for e in events])

    print(events)
    assert len(json_events) == 1
    assert isinstance(json_events, tuple)
    assert isinstance(json_events[0], dict)
    assert isinstance(json_events[0]['details'], dict)
    assert json_events[0]['code'] == 'STARTED'

    assert len(message_events) == 2
    assert isinstance(message_events, tuple)
    assert isinstance(message_events[0], dict)
    assert isinstance(message_events[0]['details'], str)


def test_process_event_list_message_only(transfer_client, mock_task_event_list):
    # Filter out the json event
    prev_events = tuple(map(lambda x: tuple(x.data.items()),
                            mock_task_event_list.return_value))
    prev_events = set(prev_events[0:1])

    (events,
     json_events,
     message_events) = _process_task_events("1234", prev_events, transfer_client)

    assert isinstance(events, set)
    assert all([isinstance(e, tuple) for e in events])
    assert all([all([isinstance(item, tuple) for item in e]) for e in events])

    assert len(json_events) == 0
    assert isinstance(json_events, tuple)

    assert len(message_events) == 2
    assert isinstance(message_events, tuple)
    assert isinstance(message_events[0], dict)
    assert isinstance(message_events[0]['details'], str)


def test_get_speed():
    speed = _get_speed({'code': "PROGRESS", 'details': {'mbps': 10}})
    assert speed == 10
    speed = _get_speed({})
    assert speed is None
    speed = _get_speed({'code': "progress", "details": "hello"})
    assert speed is None
    speed = _get_speed({'code': "progress", "details": {"hello": "world"}})
    assert speed is None
