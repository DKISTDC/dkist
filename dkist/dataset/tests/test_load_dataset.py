import shutil

import pytest
from parfive import Results

import asdf

from dkist import Dataset, TiledDataset, load_dataset
from dkist.data.test import rootdir


@pytest.fixture
def single_asdf_in_folder(tmp_path, asdf_path):
    shutil.copy(asdf_path, tmp_path)
    return tmp_path


@pytest.fixture
def multiple_asdf_in_folder(tmp_path, asdf_path):
    shutil.copy(asdf_path, tmp_path)
    shutil.copy(asdf_path, tmp_path  / "second_asdf.asdf")
    return tmp_path


@pytest.fixture
def asdf_path():
    return rootdir / "eit_dataset-1.1.0.asdf"


@pytest.fixture
def asdf_str(asdf_path):
    return asdf_path.as_posix()


@pytest.fixture
def asdf_tileddataset_path():
    return rootdir / "test_tiled_dataset-1.0.0_dataset-1.0.0.asdf"


@pytest.fixture
def single_asdf_in_folder_str(single_asdf_in_folder):
    return single_asdf_in_folder.as_posix()


@pytest.fixture
def fixture_finder(request):
    if isinstance(request.param, (list, tuple)):
        return [request.getfixturevalue(i) for i in request.param]
    return request.getfixturevalue(request.param)


@pytest.mark.parametrize("fixture_finder", [
        "asdf_path",
        "asdf_str",
        "single_asdf_in_folder",
        "single_asdf_in_folder_str",
    ],
    indirect=True
)
def test_load_single_dataset(fixture_finder):
    ds = load_dataset(fixture_finder)
    assert isinstance(ds, Dataset)


@pytest.mark.parametrize("fixture_finder", [
        ["asdf_path", "asdf_str", "single_asdf_in_folder", "single_asdf_in_folder_str"],
        ("asdf_path", "asdf_str", "single_asdf_in_folder", "single_asdf_in_folder_str"),
    ],
    indirect=True
)
def test_load_multiple(fixture_finder):
    datasets = load_dataset(fixture_finder)
    assert isinstance(datasets, list)
    assert all(isinstance(ds, Dataset) for ds in datasets)


def test_load_from_results(asdf_path, asdf_str):
    res = Results([asdf_path])
    ds = load_dataset(res)
    assert isinstance(ds, Dataset)

    res = Results([asdf_str, asdf_str])
    ds = load_dataset(res)
    assert isinstance(ds, list)
    assert all(isinstance(ds, Dataset) for ds in ds)


def test_multiple_from_dir(multiple_asdf_in_folder):
    ds = load_dataset(multiple_asdf_in_folder)
    assert isinstance(ds, list)
    assert len(ds) == 2
    assert all(isinstance(d, Dataset) for d in ds)


def test_tiled_dataset(asdf_tileddataset_path):
    ds = load_dataset(asdf_tileddataset_path)
    assert isinstance(ds, TiledDataset)


def test_errors(tmp_path):
    with pytest.raises(TypeError, match="Input type dict"):
        load_dataset({})

    with pytest.raises(ValueError, match="No asdf file found"):
        load_dataset(tmp_path)

    with pytest.raises(ValueError, match="does not exist"):
        load_dataset(tmp_path / "asdf")


def test_not_dkist_asdf(tmp_path):
    af = asdf.AsdfFile({"hello": "world"})
    af.write_to(tmp_path / "test.asdf")

    with pytest.raises(TypeError, match="not a valid DKIST"):
        load_dataset(tmp_path / "test.asdf")
