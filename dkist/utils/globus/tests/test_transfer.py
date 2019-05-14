import pathlib
from unittest import mock

import pytest

from dkist.utils.globus import start_transfer_from_file_list


@pytest.fixture
def mock_endpoints(mocker):
    def id_mock(endpoint, tc):
        return endpoint
    mocker.patch("dkist.utils.globus.transfer.auto_activate_endpoint")
    return mocker.patch("dkist.utils.globus.transfer.get_endpoint_id",
                        side_effect=id_mock)


def test_start_transfer(mocker, transfer_client, mock_endpoints):
    submit_mock = mocker.patch("globus_sdk.TransferClient.submit_transfer",
                               return_value={"task_id": "task_id"})
    file_list = list(map(pathlib.Path, ["/a/name.fits", "/a/name2.fits"]))
    start_transfer_from_file_list("a", "b", "/", file_list)
    calls = mock_endpoints.call_args_list
    assert calls[0][0][0] == "a"
    assert calls[1][0][0] == "b"

    submit_mock.assert_called_once()
    transfer_manifest = submit_mock.call_args_list[0][0][0]['DATA']

    for filepath, tfr in zip(file_list, transfer_manifest):
        assert str(filepath) == tfr['source_path']
        assert "/" + filepath.name == tfr['destination_path']


