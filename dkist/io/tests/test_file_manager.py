import logging
from pathlib import Path

import numpy as np
import pytest

from dkist import net


@pytest.fixture
def mock_inventory_refresh(mocker):
    return mocker.patch("dkist.io.file_manager.DKISTFileManager._get_inventory",
                        return_value=None)


@pytest.fixture
def orchestrate_transfer_mock(mocker):
    return mocker.patch("dkist.net.helpers._orchestrate_transfer_task",
                       autospec=True)


def test_download_default_keywords(dataset, orchestrate_transfer_mock, mock_inventory_refresh):
    base_path = Path(net.conf.dataset_path.format(**dataset.meta["inventory"]))
    folder = Path("/{bucket}/{primaryProposalId}/{datasetId}/".format(**dataset.meta["inventory"]))
    file_list = [*dataset.files.filenames, folder / "test_dataset.asdf", folder / "test_dataset.mp4", folder / "test_dataset.pdf"]
    file_list = [base_path / fn for fn in file_list]

    dataset.files.download()

    orchestrate_transfer_mock.assert_called_once_with(
        file_list,
        recursive=False,
        destination_path=Path("/~"),
        destination_endpoint=None,
        progress=True,
        wait=True,
        label=None,
    )


@pytest.fixture
def httpserver_dataset_endpoint(httpserver):
    from dkist.net import conf
    old = conf.dataset_endpoint
    conf.dataset_endpoint = httpserver.url_for("/datasets/")

    yield

    conf.dataset_endpoint = old


def test_inventory_refresh(httpserver, dataset, orchestrate_transfer_mock, httpserver_dataset_endpoint):
    dataset_id = dataset.meta["inventory"]["datasetId"]

    # Setup a happy path response
    exp = httpserver.expect_request("/datasets/v1", query_string={"datasetIds": dataset_id})
    exp.respond_with_json({"searchResults": [{"bucket": "notdata"}]})

    new_inv = dataset.files._inventory

    assert new_inv == {"bucket": "notdata"}

    assert dataset.files._inventory_cache is new_inv

    cached_inv = dataset.files._inventory

    assert cached_inv is new_inv


@pytest.mark.parametrize("error_code", [404, 202])
def test_inventory_refresh_fails(
        httpserver,
        caplog_dkist,
        dataset,
        orchestrate_transfer_mock,
        error_code,
        httpserver_dataset_endpoint
):
    dataset_id = dataset.meta["inventory"]["datasetId"]

    # Setup a happy path response
    exp = httpserver.expect_request("/datasets/v1", query_string={"datasetIds": dataset_id})
    exp.respond_with_data("Not Found", status=error_code)

    new_inv = dataset.files._get_inventory(dataset_id)
    assert ("dkist", logging.INFO, "Refreshing dataset inventory for dataset test_dataset") in caplog_dkist.record_tuples
    if error_code == 404:
        assert ("dkist",
                logging.ERROR,
                f"Inventory refresh failed with HTTP Error {error_code}: NOT FOUND") in caplog_dkist.record_tuples

    if error_code == 202:
        assert ("dkist",
                logging.ERROR,
                f"Inventory refresh failed with error code {error_code}") in caplog_dkist.record_tuples

    assert new_inv is None


@pytest.mark.parametrize("keywords", [
    {"progress": True, "wait": True, "destination_endpoint": None, "label": None},
    {"progress": True, "wait": False, "destination_endpoint": None, "label": None},
    {"progress": False, "wait": True, "destination_endpoint": None, "label": None},
    {"progress": False, "wait": True, "destination_endpoint": "wibble", "label": None},
    {"progress": False, "wait": True, "destination_endpoint": None, "label": "fibble"},
])
def test_download_keywords(dataset, orchestrate_transfer_mock, mock_inventory_refresh, keywords):
    """
    Assert that keywords are passed through as expected
    """
    base_path = Path(net.conf.dataset_path.format(**dataset.meta["inventory"]))

    folder = Path("/{bucket}/{primaryProposalId}/{datasetId}/".format(**dataset.meta["inventory"]))
    file_list = [*dataset.files.filenames, folder / "test_dataset.asdf", folder / "test_dataset.mp4", folder / "test_dataset.pdf"]
    file_list = [base_path / fn for fn in file_list]

    dataset.files.download(path="/test/", **keywords)

    orchestrate_transfer_mock.assert_called_once_with(
        file_list,
        recursive=False,
        destination_path=Path("/test"),
        **keywords
    )

    if not keywords["destination_endpoint"]:
        assert dataset.files.basepath == Path("/test/")


def test_download_path_interpolation(dataset, orchestrate_transfer_mock, mock_inventory_refresh):
    base_path = Path(net.conf.dataset_path.format(**dataset.meta["inventory"]))
    folder = Path("/{bucket}/{primaryProposalId}/{datasetId}/".format(**dataset.meta["inventory"]))
    file_list = [*dataset.files.filenames, folder / "test_dataset.asdf", folder / "test_dataset.mp4", folder / "test_dataset.pdf"]
    file_list = [base_path / fn for fn in file_list]

    dataset.files.download(path="~/{dataset_id}")

    orchestrate_transfer_mock.assert_called_once_with(
        file_list,
        recursive=False,
        destination_path=Path("~/test_dataset/"),
        destination_endpoint=None,
        progress=True,
        wait=True,
        label=None,
    )

    assert dataset.files.basepath == Path("~/test_dataset").expanduser()


def test_length_one_first_array_axis(small_visp_dataset):
    all_files = small_visp_dataset.files.filenames

    assert len(all_files) == 3

    assert len(small_visp_dataset[0:2].files.filenames) == 2

    assert len(small_visp_dataset[0].files.filenames) == 1

    assert len(small_visp_dataset[:, 5, 5].files.filenames) == 3


@pytest.mark.parametrize("kwargs", [
    {},
    {"path": "~/", "overwrite": True}
])
def test_download_quality(mocker, small_visp_dataset, kwargs):
    simple_download = mocker.patch("dkist.io.file_manager.Downloader.simple_download")
    from dkist.net import conf

    small_visp_dataset.files.quality_report(**kwargs)

    # Insert the expected default kwargs
    if kwargs.get("path") is None:
        kwargs["path"] = small_visp_dataset.files.basepath
    if "overwrite" not in kwargs:
        kwargs["overwrite"] = None

    simple_download.assert_called_once_with(
        [f"{conf.download_endpoint}/quality?datasetId={small_visp_dataset.meta['inventory']['datasetId']}"],
        **kwargs
    )


@pytest.mark.parametrize("kwargs", [
    {},
    {"path": "~/", "overwrite": True}
])
def test_download_quality_movie(mocker, small_visp_dataset, kwargs):
    simple_download = mocker.patch("dkist.io.file_manager.Downloader.simple_download")
    from dkist.net import conf

    small_visp_dataset.files.preview_movie(**kwargs)

    # Insert the expected default kwargs
    if kwargs.get("path") is None:
        kwargs["path"] = small_visp_dataset.files.basepath
    if "overwrite" not in kwargs:
        kwargs["overwrite"] = None

    simple_download.assert_called_once_with(
        [f"{conf.download_endpoint}/movie?datasetId={small_visp_dataset.meta['inventory']['datasetId']}"],
        **kwargs
    )


def test_tiled_file_manager_basepath_setter(simple_tiled_dataset):
    ds = simple_tiled_dataset
    old_basepaths = np.array([tile.files.basepath for tile in ds.flat])
    ds.files.basepath = "/some_new_path/"
    new_basepaths = np.array([tile.files.basepath for tile in ds.flat])
    assert (old_basepaths != new_basepaths).all()
    assert (new_basepaths == Path("/some_new_path/")).all()


def test_tiled_file_manager_download(large_tiled_dataset, orchestrate_transfer_mock, mock_inventory_refresh):
    ds = large_tiled_dataset
    base_path = Path(net.conf.dataset_path.format(**ds.meta["inventory"]))
    folder = Path("/{bucket}/{primaryProposalId}/{datasetId}/".format(**ds.meta["inventory"]))
    file_list = [*ds.files.filenames,
                 folder / "VBI_L1_20231016T184519_AJQWW.asdf",
                 folder / "{datasetId}.mp4".format(**ds.meta["inventory"]),
                 folder / "{datasetId}.pdf".format(**ds.meta["inventory"])]
    file_list = [base_path / fn for fn in file_list]

    ds.files.download()

    orchestrate_transfer_mock.assert_called_once_with(
        file_list,
        recursive=False,
        destination_path=ds.files.basepath,
        destination_endpoint=None,
        progress=True,
        wait=True,
        label=None,
    )
