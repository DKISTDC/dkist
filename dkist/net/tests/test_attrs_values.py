import os
import json
import shutil
import logging
import datetime
import importlib
from platform import system

import platformdirs
import pytest

from sunpy.net import attrs as a

import dkist.data
from dkist.net.attrs_values import (_fetch_values_to_file, _get_cached_json,
                                    attempt_local_update, get_search_attrs_values)

PACKAGE_FILE = importlib.resources.files(dkist.data) / "api_search_values.json"


@pytest.fixture
def tmp_homedir(tmp_path, mocker):
    if system() == "Windows":
        mocker.patch("platformdirs.user_data_path", return_value=tmp_path / "AppData")
        ori_home = os.environ.get("USERPROFILE")
        os.environ["USERPROFILE"] = str(tmp_path)
        yield tmp_path
        os.environ["USERPROFILE"] = ori_home
    else:
        ori_home = os.environ.get("HOME")
        os.environ["HOME"] = tmp_path.as_posix()
        yield tmp_path
        os.environ["HOME"] = ori_home


@pytest.fixture
def user_file(tmp_homedir):
    return platformdirs.user_data_path("dkist") / "api_search_values.json"


@pytest.fixture
def values_in_home(tmp_homedir, user_file):
    # Sanity check that platformdirs is doing what we expect
    assert tmp_homedir in user_file.parents
    user_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(PACKAGE_FILE, user_file)


def test_get_cached_json_no_local(tmp_homedir):
    return_file, update_needed = _get_cached_json()
    assert return_file == PACKAGE_FILE
    # Update is always needed if there is no local file
    assert update_needed is True


def test_get_cached_json_local(tmp_homedir, values_in_home, user_file):
    return_file, update_needed = _get_cached_json()
    assert return_file == user_file
    # We just copied the file so shouldn't need an update
    assert update_needed is False


def test_get_cached_json_local_out_of_date(tmp_homedir, values_in_home, user_file):
    ten_ago = (datetime.datetime.now() - datetime.timedelta(days=10)).timestamp()
    os.utime(user_file, (ten_ago, ten_ago))
    return_file, update_needed = _get_cached_json()
    assert return_file == user_file
    # We changed mtime, so we need an update
    assert update_needed is True


def test_get_cached_json_local_not_quite_out_of_date(tmp_homedir, values_in_home, user_file):
    ten_ago = (datetime.datetime.now() - datetime.timedelta(days=6)).timestamp()
    os.utime(user_file, (ten_ago, ten_ago))
    return_file, update_needed = _get_cached_json()
    assert return_file == user_file
    # We changed mtime, so we need don't an update
    assert update_needed is False


@pytest.mark.remote_data
def test_fetch_values_to_file(tmp_path):
    json_file = tmp_path / "api_search_values.json"

    assert json_file.exists() is False
    _fetch_values_to_file(json_file)
    assert json_file.exists() is True

    # Check we can load the file as json and it looks very roughly like what we
    # would expect from the API response
    with open(json_file) as f:
        data = json.load(f)
    assert "parameterValues" in data.keys()
    assert isinstance(data["parameterValues"], list)


def _local_fetch_values(user_file, *, timeout):
    user_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(PACKAGE_FILE, user_file)


def test_attempt_local_update(mocker, tmp_path, caplog_dkist):
    json_file = tmp_path / "api_search_values.json"
    mocker.patch("dkist.net.attrs_values._fetch_values_to_file",
                 new_callable=lambda: _local_fetch_values)
    success = attempt_local_update(user_file=json_file, silence_errors=False)
    assert success

    assert caplog_dkist.record_tuples == [
        ("dkist", logging.INFO, f"Fetching updated search values for the DKIST client to {json_file}")
    ]


def raise_error(*args, **kwargs):
    raise ValueError("This is a value error")


def test_attempt_local_update_error_download(mocker, caplog_dkist, tmp_homedir, user_file):
    mocker.patch("dkist.net.attrs_values._fetch_values_to_file",
                 side_effect=raise_error)
    success = attempt_local_update(silence_errors=True)
    assert not success

    assert caplog_dkist.record_tuples == [
        ("dkist", logging.INFO, f"Fetching updated search values for the DKIST client to {user_file}"),
        ("dkist", logging.ERROR, "Failed to download new attrs values."),
    ]

    with pytest.raises(ValueError, match="This is a value error"):
        success = attempt_local_update(silence_errors=False)


def _definately_not_json(user_file, *, timeout):
    with open(user_file, "w") as f:
        f.write("This is not json")


def test_attempt_local_update_fail_invalid_download(mocker, tmp_path, caplog_dkist):
    json_file = tmp_path / "api_search_values.json"
    mocker.patch("dkist.net.attrs_values._fetch_values_to_file",
                 new_callable=lambda: _definately_not_json)
    success = attempt_local_update(user_file=json_file, silence_errors=True)
    assert not success

    assert caplog_dkist.record_tuples == [
        ("dkist", logging.INFO, f"Fetching updated search values for the DKIST client to {json_file}"),
        ("dkist", logging.ERROR, "Downloaded file is not valid JSON."),
    ]

    with pytest.raises(json.JSONDecodeError):
        success = attempt_local_update(user_file=json_file, silence_errors=False)


@pytest.mark.parametrize(("user_file", "update_needed", "allow_update", "should_update"), [
    ("user_file", False, True, False),
    ("user_file", True, True, True),
    ("user_file", True, False, False),
], indirect=["user_file"])
def test_get_search_attrs_values(mocker, caplog_dkist, values_in_home, user_file, update_needed, allow_update, should_update):
    mocker.patch("dkist.net.attrs_values._get_cached_json",
                 new_callable=lambda: lambda: (user_file, update_needed))

    alu_mock = mocker.patch("dkist.net.attrs_values.attempt_local_update")

    attr_values = get_search_attrs_values(allow_update=allow_update)

    if should_update:
        alu_mock.assert_called_once()
    else:
        alu_mock.assert_not_called()

    assert isinstance(attr_values, dict)
    # Test that some known attrs are in the result
    assert {a.Instrument, a.dkist.HeaderVersion, a.dkist.WorkflowName}.issubset(attr_values.keys())
