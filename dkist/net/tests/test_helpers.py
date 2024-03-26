import datetime
from pathlib import Path

import pytest

from sunpy.net.fido_factory import UnifiedResponse

from dkist.net.client import DKISTClient, DKISTQueryResponseTable
from dkist.net.helpers import transfer_complete_datasets


@pytest.fixture
def orchestrate_transfer_mock(mocker):
    return mocker.patch("dkist.net.helpers._orchestrate_transfer_task", autospec=True)


@pytest.mark.parametrize(
    "keywords",
    [
        {"progress": True, "wait": True, "destination_endpoint": None, "label": None},
        {"progress": True, "wait": False, "destination_endpoint": None, "label": None},
        {"progress": False, "wait": True, "destination_endpoint": None, "label": None},
        {"progress": False, "wait": True, "destination_endpoint": "wibble", "label": None},
        {"progress": False, "wait": True, "destination_endpoint": None, "label": "fibble"},
    ],
)
def test_download_default_keywords(orchestrate_transfer_mock, keywords):
    transfer_complete_datasets(
        DKISTQueryResponseTable([
            {
                "Dataset ID": "AAAA",
                "Primary Proposal ID": "pm_1_10",
                "Storage Bucket": "data",
                "Wavelength Max": 856,
                "Wavelength Min": 854,
            }
        ]),
        **keywords
    )

    if keywords["label"] is None:
        keywords["label"] = f"DKIST Python Tools - {datetime.datetime.now().strftime('%Y-%m-%dT%H-%M')} AAAA"
    orchestrate_transfer_mock.assert_called_once_with(
        [Path("/data/pm_1_10/AAAA")],
        recursive=True,
        destination_path=Path("/~"),
        **keywords
    )


def test_transfer_unavailable_data(mocker):
    mocker.patch(
        "dkist.net.client.DKISTClient.search",
        autospec=True,
        return_value=[],
    )

    with pytest.raises(ValueError, match="No results available for dataset"):
        transfer_complete_datasets("null")


def test_transfer_from_dataset_id(mocker, orchestrate_transfer_mock):
    get_inv_mock = mocker.patch(
        "dkist.net.helpers._get_dataset_inventory",
        autospec=True,
        return_value=DKISTQueryResponseTable([
            {
                "Dataset ID": "AAAA",
                "Primary Proposal ID": "pm_1_10",
                "Storage Bucket": "data",
                "Wavelength Max": 856,
                "Wavelength Min": 854,
            }
        ]),
    )

    transfer_complete_datasets("AAAA")

    orchestrate_transfer_mock.assert_called_once_with(
        [Path("/data/pm_1_10/AAAA")],
        recursive=True,
        destination_path=Path("/~"),
        destination_endpoint=None,
        progress=True,
        wait=True,
        label=f"DKIST Python Tools - {datetime.datetime.now().strftime('%Y-%m-%dT%H-%M')} AAAA"
    )

    get_inv_mock.assert_called_once_with("AAAA")


def test_transfer_from_multiple_dataset_id(mocker, orchestrate_transfer_mock):
    get_inv_mock = mocker.patch(
        "dkist.net.helpers._get_dataset_inventory",
        autospec=True,
        return_value=DKISTQueryResponseTable([
            {
                "Dataset ID": "AAAA",
                "Primary Proposal ID": "pm_1_10",
                "Storage Bucket": "data",
                "Wavelength Max": 856,
                "Wavelength Min": 854,
            },
            {
                "Dataset ID": "BBBB",
                "Primary Proposal ID": "pm_1_10",
                "Storage Bucket": "data",
                "Wavelength Max": 856,
                "Wavelength Min": 854,
            }
        ]),
    )

    transfer_complete_datasets(["AAAA", "BBBB"])

    orchestrate_transfer_mock.assert_has_calls(
        [
            mocker.call(
                [Path("/data/pm_1_10/AAAA")],
                recursive=True,
                destination_path=Path("/~"),
                destination_endpoint=None,
                progress=True,
                wait=True,
                label=f"DKIST Python Tools - {datetime.datetime.now().strftime('%Y-%m-%dT%H-%M')} AAAA",
            ),
            mocker.call(
                [Path("/data/pm_1_10/BBBB")],
                recursive=True,
                destination_path=Path("/~"),
                destination_endpoint=None,
                progress=True,
                wait=True,
                label=f"DKIST Python Tools - {datetime.datetime.now().strftime('%Y-%m-%dT%H-%M')} BBBB",
            ),
        ]
    )

    get_inv_mock.assert_called_once_with(["AAAA", "BBBB"])


def test_transfer_from_table(orchestrate_transfer_mock, mocker):
    res = DKISTQueryResponseTable(
        {
            "Dataset ID": ["A", "B"],
            "Primary Proposal ID": ["pm_1_10", "pm_2_20"],
            "Storage Bucket": ["data", "data"],
            "Wavelength Max": [856, 856],
            "Wavelength Min": [854, 854],
        },
    )

    transfer_complete_datasets(res, label="fibble")

    kwargs = {"progress": True, "wait": True, "destination_endpoint": None, "label": "fibble"}
    orchestrate_transfer_mock.assert_has_calls(
        [
            mocker.call(
                [Path("/data/pm_1_10/A")],
                recursive=True,
                destination_path=Path("/~"),
                **kwargs
            ),
            mocker.call(
                [Path("/data/pm_2_20/B")],
                recursive=True,
                destination_path=Path("/~"),
                **kwargs
            ),
        ]
    )


def test_transfer_from_length_one_table(orchestrate_transfer_mock, mocker):
    res = DKISTQueryResponseTable(
        {
            "Dataset ID": ["A"],
            "Primary Proposal ID": ["pm_1_10"],
            "Storage Bucket": ["data"],
            "Wavelength Max": [856],
            "Wavelength Min": [854],
        },
    )

    transfer_complete_datasets(res, label="fibble")

    kwargs = {"progress": True, "wait": True, "destination_endpoint": None, "label": "fibble"}
    orchestrate_transfer_mock.assert_has_calls(
        [
            mocker.call(
                [Path("/data/pm_1_10/A")],
                recursive=True,
                destination_path=Path("/~"),
                **kwargs
            ),
        ]
    )


def test_transfer_from_row(orchestrate_transfer_mock, mocker):
    res = DKISTQueryResponseTable(
        {
            "Dataset ID": ["A"],
            "Primary Proposal ID": ["pm_1_10"],
            "Storage Bucket": ["data"],
            "Wavelength Max": [856],
            "Wavelength Min": [854],
        },
    )

    transfer_complete_datasets(res[0], label="fibble")

    kwargs = {"progress": True, "wait": True, "destination_endpoint": None, "label": "fibble"}
    orchestrate_transfer_mock.assert_has_calls(
        [
            mocker.call(
                [Path("/data/pm_1_10/A")],
                recursive=True,
                destination_path=Path("/~"),
                **kwargs
            ),
        ]
    )


def test_transfer_from_UnifiedResponse(orchestrate_transfer_mock, mocker):
    res = UnifiedResponse(
        DKISTQueryResponseTable(
            {
                "Dataset ID": ["A"],
                "Primary Proposal ID": ["pm_1_10"],
                "Storage Bucket": ["data"],
            "Wavelength Max": [856],
            "Wavelength Min": [854],
            },
        ),
        DKISTQueryResponseTable(
            {
                "Dataset ID": ["B"],
                "Primary Proposal ID": ["pm_2_20"],
                "Storage Bucket": ["data"],
            "Wavelength Max": [856],
            "Wavelength Min": [854],
            },
        ),
    )
    res._list[0].client = res._list[1].client = DKISTClient()

    transfer_complete_datasets(res, label="fibble")

    kwargs = {"progress": True, "wait": True, "destination_endpoint": None, "label": "fibble"}
    orchestrate_transfer_mock.assert_has_calls(
        [
            mocker.call(
                [Path("/data/pm_1_10/A")],
                recursive=True,
                destination_path=Path("/~"),
                **kwargs
            ),
            mocker.call(
                [Path("/data/pm_2_20/B")],
                recursive=True,
                destination_path=Path("/~"),
                **kwargs
            ),
        ]
    )


def test_transfer_path_interpolation(orchestrate_transfer_mock, mocker):
    get_inv_mock = mocker.patch(
        "dkist.net.helpers._get_dataset_inventory",
        autospec=True,
        return_value=DKISTQueryResponseTable([
            {
                "Dataset ID": "AAAA",
                "Primary Proposal ID": "pm_1_10",
                "Storage Bucket": "data",
                "Wavelength Max": 856,
                "Wavelength Min": 854,
                "Instrument": "HIT",  # Highly Imaginary Telescope
            }
        ]),
    )

    transfer_complete_datasets("AAAA", path="{instrument}/{dataset_id}")

    orchestrate_transfer_mock.assert_called_once_with(
        [Path("/data/pm_1_10/AAAA")],
        recursive=True,
        destination_path=Path("HIT/AAAA"),
        destination_endpoint=None,
        progress=True,
        wait=True,
        label=f"DKIST Python Tools - {datetime.datetime.now().strftime('%Y-%m-%dT%H-%M')} AAAA"
    )

    get_inv_mock.assert_called_once_with("AAAA")
