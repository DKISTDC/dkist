import os
import json
import shutil
import logging
import datetime
import importlib
from platform import system
from urllib.error import URLError

import platformdirs
import pytest

from sunpy.net import attrs as a

import dkist.data
from dkist.net.attrs_values import (UserCacheMissing, _fetch_values, _get_cached_json,
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
def test_fetch_values_to_file():
    data = _fetch_values()
    assert isinstance(data, bytes)

    jdata = json.loads(data)
    assert "parameterValues" in jdata.keys()
    assert isinstance(jdata["parameterValues"], list)


def _local_fetch_values(timeout):
    with open(PACKAGE_FILE, "rb") as fobj:
        return fobj.read()


def test_attempt_local_update(mocker, tmp_path, caplog_dkist):
    json_file = tmp_path / "api_search_values.json"
    mocker.patch("dkist.net.attrs_values._fetch_values",
                 new_callable=lambda: _local_fetch_values)
    success = attempt_local_update(user_file=json_file, silence_net_errors=False)
    assert success

    assert caplog_dkist.record_tuples == [
        ("dkist", logging.INFO, f"Fetching updated search values for the DKIST client to {json_file}")
    ]


def raise_error(*args, **kwargs):
    raise ValueError("This is a value error")


def test_attempt_local_update_error_download(mocker, caplog_dkist, tmp_homedir, user_file):
    mocker.patch("dkist.net.attrs_values._fetch_values",
                 side_effect=raise_error)
    success = attempt_local_update(silence_net_errors=True)
    assert not success

    assert caplog_dkist.record_tuples == [
        ("dkist", logging.INFO, f"Fetching updated search values for the DKIST client to {user_file}"),
        ("dkist", logging.ERROR, "Failed to download new dkist attrs values. attr values for dkist may be outdated."),
    ]

    with pytest.raises(ValueError, match="This is a value error"):
        success = attempt_local_update(silence_net_errors=False)


def _definitely_not_json(timeout):
    return b"alskdjalskdjaslkdj!!"


def test_attempt_local_update_fail_invalid_json(mocker, user_file, tmp_path, caplog_dkist):
    # test that the file is removed after
    json_file = tmp_path / "api_search_values.json"
    mocker.patch("dkist.net.attrs_values._fetch_values",
                 new_callable=lambda: _definitely_not_json)
    with pytest.raises(UserCacheMissing):
        success = attempt_local_update(user_file=json_file)

    # File should have been deleted if the update has got as far as returning this error
    assert not json_file.exists()


def test_get_search_attrs_values_fail_invalid_download(mocker, user_file, values_in_home, tmp_path, caplog_dkist):
    """
    Given: An existing cache file
    When: JSON is invalid
    Then: File is removed, and attr values are still loaded
    """
    mocker.patch("dkist.net.attrs_values._fetch_values",
                 new_callable=lambda: _definitely_not_json)
    ten_ago = (datetime.datetime.now() - datetime.timedelta(days=10)).timestamp()
    os.utime(user_file, (ten_ago, ten_ago))

    attr_values = get_search_attrs_values()
    assert not user_file.exists()

    assert {a.Instrument, a.dkist.HeaderVersion, a.dkist.WorkflowName}.issubset(attr_values.keys())


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


def _fetch_values_urlerror(*args):
    raise URLError("it hates you")


def test_failed_download(mocker, caplog_dkist, user_file, values_in_home):
    mock = mocker.patch("dkist.net.attrs_values._fetch_values",
                        new_callable=lambda: _fetch_values_urlerror)

    ten_ago = (datetime.datetime.now() - datetime.timedelta(days=10)).timestamp()
    os.utime(user_file, (ten_ago, ten_ago))

    attr_values = get_search_attrs_values(allow_update=True)

    assert caplog_dkist.record_tuples == [
        ("dkist", logging.INFO, f"Fetching updated search values for the DKIST client to {user_file}"),
        ("dkist", logging.ERROR, "Failed to download new dkist attrs values. attr values for dkist may be outdated."),
    ]
