from pathlib import Path

import pytest

from dkist.net.helpers import transfer_whole_dataset


@pytest.fixture
def orchestrate_transfer_mock(mocker):
    yield mocker.patch("dkist.net.helpers._orchestrate_transfer_task",
                       autospec=True)


@pytest.mark.parametrize("keywords", [
    {"progress": True, "wait": True, "destination_endpoint": None},
    {"progress": True, "wait": False, "destination_endpoint": None},
    {"progress": False, "wait": True, "destination_endpoint": None},
    {"progress": False, "wait": True, "destination_endpoint": "wibble"},
])
def test_download_default_keywords(orchestrate_transfer_mock, keywords):
    transfer_whole_dataset(
        {
            "Dataset ID": "AAAA",
            "Primary Proposal ID": "pm_1_10",
            "Storage Bucket": "data"
        },
        **keywords
    )

    orchestrate_transfer_mock.assert_called_once_with(
        [Path("/data/pm_1_10/AAAA")],
        recursive=True,
        destination_path=Path('/~/pm_1_10'),
        **keywords
    )


def test_transfer_from_dataset_id(mocker, orchestrate_transfer_mock):
    get_inv_mock = mocker.patch("dkist.net.helpers._get_dataset_inventory",
                                autospec=True,
                                return_value=[{
                                    "Dataset ID": "AAAA",
                                    "Primary Proposal ID": "pm_1_10",
                                    "Storage Bucket": "data"
                                }])

    transfer_whole_dataset("AAAA")

    orchestrate_transfer_mock.assert_called_once_with(
        [Path("/data/pm_1_10/AAAA")],
        recursive=True,
        destination_path=Path('/~/pm_1_10'),
        destination_endpoint=None,
        progress=True,
        wait=True,
    )

    get_inv_mock.assert_called_once_with("AAAA")
