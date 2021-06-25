"""
Globus Auth Helpers.
"""
# A lot of this code is copied from the Globus Auth Example repo:
# https://github.com/globus/native-app-examples

import json
import stat
import queue
import functools
import threading
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

import appdirs
import globus_sdk
import globus_sdk.auth.token_response

CLIENT_ID = 'dd2d62af-0b44-4e2e-9454-1092c94b46b3'
SCOPES = ('urn:globus:auth:scope:transfer.api.globus.org:all',
          'openid')


__all__ = ['ensure_globus_authorized', 'get_refresh_token_authorizer']


class AuthenticationError(Exception):
    """
    An error to be raised if authentication fails.
    """


class RedirectHTTPServer(HTTPServer):
    def __init__(self, listen, handler_class):
        super().__init__(listen, handler_class)

        self._auth_code_queue = queue.Queue()

    def return_code(self, code):
        self._auth_code_queue.put_nowait(code)

    def wait_for_code(self):
        return self._auth_code_queue.get(block=True)


class RedirectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'You\'re all set, you can close this window!')

        code = parse_qs(urlparse(self.path).query).get('code', [''])[0]
        self.server.return_code(code)

    def log_message(self, format, *args):
        return


def start_local_server(listen=('localhost', 0)):
    """
    Start a server which will listen for the OAuth2 callback.

    Parameters
    ----------
    listen: `tuple`, optional
        ``(address, port)`` tuple, defaults to localhost and port 0, which
        leads to the system choosing a free port.
    """
    server = RedirectHTTPServer(listen, RedirectHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    return server


def get_cache_file_path():
    """
    Use appdirs to get the cache path for the user and add the filename.
    """
    cache_dir = Path(appdirs.user_cache_dir("dkist"))
    return cache_dir / "globus_auth_cache.json"


def get_cache_contents():
    """
    Read the cache file, return an empty dict if not found or invalid.
    """
    cache_file = get_cache_file_path()
    if not cache_file.exists():
        return {}
    else:
        try:
            with open(cache_file) as fd:
                return json.load(fd)
        except (IOError, json.JSONDecodeError):
            return {}


def save_auth_cache(auth_cache):
    """
    Write the auth cache to the cache file.

    Parameters
    ----------
    auth_cache: `dict` or `~globus_sdk.auth.token_response.OAuthTokenResponse`
        The auth cache to save.

    """
    if isinstance(auth_cache, globus_sdk.auth.token_response.OAuthTokenResponse):
        auth_cache = auth_cache.by_resource_server

    cache_file = get_cache_file_path()

    # Ensure the cache dir exists.
    cache_dir = cache_file.parent
    if not cache_dir.exists():
        cache_dir.mkdir(parents=True)

    # Write the token to the cache file.
    with open(cache_file, "w") as fd:
        json.dump(auth_cache, fd)

    # Ensure the token file has minimal permissions.
    cache_file.chmod(stat.S_IRUSR | stat.S_IWUSR)


def do_native_app_authentication(client_id, requested_scopes=None):  # pragma: no cover
    """
    Does a Native App authentication flow and returns a
    dict of tokens keyed by service name.
    """
    server = start_local_server()
    redirect_uri = "http://{a[0]}:{a[1]}".format(a=server.server_address)

    client = globus_sdk.NativeAppAuthClient(client_id=client_id)
    client.oauth2_start_flow(requested_scopes=SCOPES,
                             redirect_uri=redirect_uri,
                             refresh_tokens=True)
    url = client.oauth2_get_authorize_url()

    result = webbrowser.open(url, new=1)
    print("Waiting for completion of Globus Authentication in your webbrowser...")
    print(f"If your webbrowser has not opened, please go to {url} to authenticate with globus.")

    try:
        auth_code = server.wait_for_code()
    except KeyboardInterrupt:
        raise AuthenticationError("Failed to authenticate with Globus.")
    finally:
        server.shutdown()

    token_response = client.oauth2_exchange_code_for_tokens(auth_code)

    # return a set of tokens, organized by resource server name
    return token_response.by_resource_server


def get_refresh_token_authorizer(force_reauth=False):
    """
    Perform OAuth2 Authentication to Globus.

    Parameters
    ----------
    force_reauth: `bool`, optional
        If `True` ignore any cached credentials and reauth with Globus. This is
        useful if the cache is corrupted or the refresh token has expired.

    Returns
    -------
    `globus_sdk.RefreshTokenAuthorizer`

    """
    tokens = None
    if not force_reauth:
        tokens = get_cache_contents()
    if not tokens:
        tokens = do_native_app_authentication(CLIENT_ID, SCOPES)
        save_auth_cache(tokens)

    auth_client = globus_sdk.NativeAppAuthClient(client_id=CLIENT_ID)

    transfer_tokens = tokens['transfer.api.globus.org']

    authorizers = {}
    for scope, transfer_tokens in tokens.items():
        authorizers[scope] = globus_sdk.RefreshTokenAuthorizer(
            transfer_tokens['refresh_token'],
            auth_client,
            access_token=transfer_tokens['access_token'],
            expires_at=transfer_tokens['expires_at_seconds'],
            on_refresh=save_auth_cache)

    return authorizers


def ensure_globus_authorized(func):
    """
    A wrapper for functions that need valid globus authorization.

    If the refresh token is invalid this function will prompt the user to
    login.
    """
    @functools.wraps(func)
    def do_reauth(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except globus_sdk.AuthAPIError as e:
            if e.http_status == 400 and e.message == "invalid_grant":
                print("Globus login has expired.")
                get_refresh_token_authorizer(force_reauth=True)
                return func(*args, **kwargs)

    return do_reauth
