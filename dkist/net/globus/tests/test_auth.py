import json
import stat
import pathlib
import platform

import globus_sdk
import requests

from dkist.net.globus.auth import (ensure_globus_authorized, get_cache_contents,
                                   get_cache_file_path, get_refresh_token_authorizer,
                                   save_auth_cache, start_local_server)


def test_http_server():
    server = start_local_server()
    redirect_uri = f"http://{server.server_address[0]}:{server.server_address[1]}"
    inp_code = "wibble"

    requests.get(redirect_uri + f"?code={inp_code}")

    code = server.wait_for_code()

    assert code == inp_code


def test_get_cache_file_path(mocker):
    mocker.patch("platformdirs.user_cache_dir", return_value="/tmp/test/")
    path = get_cache_file_path()
    assert isinstance(path, pathlib.Path)

    assert path.parent == pathlib.Path("/tmp/test")
    assert path.name == "globus_auth_cache.json"


def test_get_no_cache(mocker, tmpdir):
    mocker.patch("platformdirs.user_cache_dir", return_value=str(tmpdir))
    # Test file not exists
    cache = get_cache_contents()
    assert isinstance(cache, dict)
    assert not cache


def test_get_cache(mocker, tmpdir):
    mocker.patch("platformdirs.user_cache_dir", return_value=str(tmpdir))
    with open(tmpdir / "globus_auth_cache.json", "w") as fd:
        json.dump({"hello": "world"}, fd)

    cache = get_cache_contents()
    assert isinstance(cache, dict)
    assert len(cache) == 1
    assert cache == {"hello": "world"}


def test_get_cache_not_json(mocker, tmpdir):
    mocker.patch("platformdirs.user_cache_dir", return_value=str(tmpdir))
    with open(tmpdir / "globus_auth_cache.json", "w") as fd:
        fd.write("aslkjdasdjjdlsajdjklasjdj, akldjaskldjasd, lkjasdkljasldkjas")

    cache = get_cache_contents()
    assert isinstance(cache, dict)
    assert not cache


def test_save_auth_cache(mocker, tmpdir):
    filename = tmpdir / "globus_auth_cache.json"
    assert not filename.exists()  # Sanity check
    mocker.patch("platformdirs.user_cache_dir", return_value=str(tmpdir))
    save_auth_cache({"hello": "world"})

    assert filename.exists()
    statinfo = filename.stat()

    # Test that the user can read and write
    assert bool(statinfo.mode & stat.S_IRUSR)
    assert bool(statinfo.mode & stat.S_IWUSR)

    if platform.system() != "Windows":
        # Test that neither "Group" or "Other" have read permissions
        assert not bool(statinfo.mode & stat.S_IRGRP)
        assert not bool(statinfo.mode & stat.S_IROTH)


def test_get_refresh_token_authorizer(mocker):
    # An example cache without real tokens
    cache = {
        "transfer.api.globus.org": {
            "scope": "urn:globus:auth:scope:transfer.api.globus.org:all",
            "access_token": "buscVeATmhfB0v1tzu8VmTfFRB1nwlF8bn1R9rQTI3Q",
            "refresh_token": "YSbLZowAHfmhxehUqeOF3lFvoC0FlTT11QGupfWAOX4",
            "token_type": "Bearer",
            "expires_at_seconds": 1553362861,
            "resource_server": "transfer.api.globus.org"
        }
    }

    mocker.patch("dkist.net.globus.auth.get_cache_contents", return_value=cache)
    auth = get_refresh_token_authorizer()["transfer.api.globus.org"]
    assert isinstance(auth, globus_sdk.RefreshTokenAuthorizer)
    assert auth.access_token == cache["transfer.api.globus.org"]["access_token"]

    mocker.patch("dkist.net.globus.auth.do_native_app_authentication", return_value=cache)
    auth = get_refresh_token_authorizer(force_reauth=True)["transfer.api.globus.org"]
    assert isinstance(auth, globus_sdk.RefreshTokenAuthorizer)
    assert auth.access_token == cache["transfer.api.globus.org"]["access_token"]


def test_ensure_auth_decorator(mocker):
    mock_response = mocker.MagicMock()
    mock_response.status_code = 400
    mock_response.text = '{"error": "invalid_grant"}'
    mock_response.json = mocker.Mock(return_value=json.loads(mock_response.text))
    mock_response.headers = {"Content-Type": "application/json"}
    error = globus_sdk.AuthAPIError(mock_response)
    reauth = mocker.patch("dkist.net.globus.auth.get_refresh_token_authorizer")

    called = [False]
    @ensure_globus_authorized
    def test_func():
        if not called[0]:
            called[0] = True
            raise error
        return True

    assert test_func()
    reauth.assert_called_once_with(force_reauth=True)
