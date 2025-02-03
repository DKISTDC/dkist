import re
import shutil
import numbers

import pytest
from parfive import Results

import asdf

from dkist import Dataset, TiledDataset, load_dataset
from dkist.data.test import rootdir
from dkist.dataset.loader import ASDF_FILENAME_PATTERN
from dkist.utils.exceptions import DKISTUserWarning


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


def generate_asdf_folder(tmp_path, asdf_path, filenames):
    for fname in filenames:
        shutil.copy(asdf_path, tmp_path / fname)

    return tmp_path


@pytest.mark.parametrize(("filename", "match"), [
    ("VBI_L1_20231016T184519_AJQWW.asdf", True),
    ("VBI_L1_20231016T184519_AAAA.asdf", False),
    ("VBI_L1_20231016T184519_AJQWW_user_tools.asdf", True),
    ("VBI_L1_20231016T184519_AJQWW_metadata.asdf", True),
    ("DL-NIRSP_L1_20231016T184519_AJQWW.asdf", True),
    ("DL-NIRSP_L1_20231016T184519_AJQWW_user_tools.asdf", True),
    ("DL-NIRSP_L1_20231016T184519_AJQWW_metadata.asdf", True),
    ("VISP_L1_99999999T184519_AAAAAAA.asdf", True),
    ("VISP_L1_20231016T888888_AAAAAAA_user_tools.asdf", True),
    ("VISP_L1_20231016T184519_AAAAAAA_metadata.asdf", True),
    ("VISP_L1_20231016T184519_AAAAAAA_unknown.asdf", False),
    ("VISP_L1_20231016T184519.asdf", False),
    ("wibble.asdf", False),
    ])
def test_asdf_regex(filename, match):
    m = re.match(ASDF_FILENAME_PATTERN, filename)
    assert bool(m) is match


@pytest.mark.parametrize(("filenames", "indices"), [
    pytest.param(("VBI_L1_20231016T184519_AJQWW.asdf",), 0, id="Single no suffix"),
    pytest.param(("VBI_L1_20231016T184519_AJQWW_user_tools.asdf",), 0, id="single _user_tools"),
    pytest.param(("VBI_L1_20231016T184519_AJQWW_metadata.asdf",), 0, id="single _metadata"),
    pytest.param(("VBI_L1_20231016T184519_AJQWW_unknown.asdf",), 0, id="single _unknown"),
    pytest.param(("VBI_L1_20231016T184519_AJQWW.asdf",
                  "VBI_L1_20231016T184519_AJQWW_user_tools.asdf",), 1, id="none & _user_tools"),
    pytest.param(("VBI_L1_20231016T184519_AJQWW.asdf",
                  "VBI_L1_20231016T184519_AJQWW_user_tools.asdf",
                  "VBI_L1_20231016T184519_AJQWW_metadata.asdf",), 2, id="_user_tools & _metadata"),
    pytest.param(("VBI_L1_20231016T184519_AJQWW.asdf",
                  "VBI_L1_20231016T184519_AJQWW_user_tools.asdf",
                  "VBI_L1_20231016T184519_AJQWW_metadata.asdf",
                  "VBI_L1_20231016T184519_AJQWW_unknown.asdf"), (2, 3), id="_user_tools & _metadata & _unknown"),
    pytest.param(("random.asdf",
                  "VBI_L1_20231016T184519_AJQWW_user_tools.asdf",), (0, 1), id="other pattern & _user_tools"),
    pytest.param(("random.asdf",
                  "VBI_L1_not_a_proper_name.asdf",
                  "VBI_L1_20231016T184519_AJQWW_user_tools.asdf",
                  "VBI_L1_20231016T184519_AJQWW_metadata.asdf",), (0, 1, 3), id="2 other patterns & _user_tools & _metadata"),
    pytest.param(("VBI_L1_20231016T184519_AJQWW.asdf",
                  "VISP_L1_20231016T184519_AJQWW.asdf",), (0, 1), id="Two patterns, no suffix"),
    pytest.param(("VBI_L1_20231016T184519_AAAAA.asdf",
                  "VBI_L1_20231016T184519_AAAAA_metadata.asdf",
                  "VBI_L1_20231116T184519_BBBBBBB.asdf",
                  "VBI_L1_20231216T184519_CCCCCCC.asdf",
                  "VBI_L1_20231216T184519_CCCCCCC_user_tools.asdf"), (1, 2, 4), id="Three patterns, mixed suffixes"),
])
def test_select_asdf(tmp_path, asdf_path, filenames, indices, mocker):
    asdf_folder = generate_asdf_folder(tmp_path, asdf_path, filenames)

    asdf_file_paths = tuple(asdf_folder / fname for fname in filenames)

    load_from_asdf = mocker.patch("dkist.dataset.loader._load_from_asdf")
    load_from_iterable = mocker.patch("dkist.dataset.loader._load_from_iterable")

    # The load_dataset call should throw a warning if any files are skipped, but
    # not otherwise, the warning should have the filenames of any skipped files in
    tuple_of_indices = indices if isinstance(indices, tuple) else (indices,)
    if len(tuple_of_indices) == len(filenames):
        datasets = load_dataset(asdf_folder)
    else:
        files_to_be_skipped = set(filenames).difference([filenames[i] for i in tuple_of_indices])
        with pytest.warns(DKISTUserWarning, match=f".*[{'|'.join([re.escape(f) for f in files_to_be_skipped])}].*"):
            datasets = load_dataset(asdf_folder)

    if isinstance(indices, numbers.Integral):
        load_from_asdf.assert_called_once_with(asdf_file_paths[indices])
    else:
        calls = load_from_iterable.mock_calls
        # We need to assert that _load_from_iterable is called with the right
        # paths but in a order-invariant way.
        assert len(calls) == 1
        assert set(calls[0].args[0]) == {asdf_file_paths[i] for i in indices}
