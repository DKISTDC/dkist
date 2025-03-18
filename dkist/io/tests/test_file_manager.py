from pathlib import Path

import pytest

from dkist import net


@pytest.fixture
def orchestrate_transfer_mock(mocker):
    return mocker.patch("dkist.net.helpers._orchestrate_transfer_task",
                       autospec=True)


def test_download_default_keywords(dataset, orchestrate_transfer_mock):
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


@pytest.mark.parametrize("keywords", [
    {"progress": True, "wait": True, "destination_endpoint": None, "label": None},
    {"progress": True, "wait": False, "destination_endpoint": None, "label": None},
    {"progress": False, "wait": True, "destination_endpoint": None, "label": None},
    {"progress": False, "wait": True, "destination_endpoint": "wibble", "label": None},
    {"progress": False, "wait": True, "destination_endpoint": None, "label": "fibble"},
])
def test_download_keywords(dataset, orchestrate_transfer_mock, keywords):
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


def test_download_path_interpolation(dataset, orchestrate_transfer_mock):
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
