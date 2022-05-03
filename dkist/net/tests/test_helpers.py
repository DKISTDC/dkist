from pathlib import Path

import pytest

from dkist.net.client import DKISTQueryResponseTable
from dkist.net.helpers import transfer_complete_datasets


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
    transfer_complete_datasets(
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

    transfer_complete_datasets("AAAA")

    orchestrate_transfer_mock.assert_called_once_with(
        [Path("/data/pm_1_10/AAAA")],
        recursive=True,
        destination_path=Path('/~/pm_1_10'),
        destination_endpoint=None,
        progress=True,
        wait=True,
    )

    get_inv_mock.assert_called_once_with("AAAA")


def test_transfer_from_table(orchestrate_transfer_mock, mocker):
    res = DKISTQueryResponseTable(
        {
            "Dataset ID": ["A", "B"],
            "Primary Proposal ID": ["pm_1_10", "pm_2_20"],
            "Storage Bucket": ["data", "data"],
        },
    )

    transfer_complete_datasets(res)

    kwargs = {"progress": True, "wait": True, "destination_endpoint": None}
    orchestrate_transfer_mock.assert_has_calls(
        [
            mocker.call(
                [Path("/data/pm_1_10/A")],
                recursive=True,
                destination_path=Path('/~/pm_1_10'),
                **kwargs
            ),
            mocker.call(
                [Path("/data/pm_2_20/B")],
                recursive=True,
                destination_path=Path('/~/pm_2_20'),
                **kwargs
            ),
        ]
    )
