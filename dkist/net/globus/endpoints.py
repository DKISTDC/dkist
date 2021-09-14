"""
Functions for interacting with globus endpoints.
"""
import pathlib
import webbrowser

import globus_sdk

from .auth import ensure_globus_authorized, get_refresh_token_authorizer

__all__ = ['get_endpoint_id', 'get_directory_listing']


def get_transfer_client(force_reauth=False):
    """
    Get an authorized transfer client.

    Parameters
    ----------
    force_reauth : `bool`, optional
        Do not use cached authentication details when `True`.

    Returns
    -------
    `globus_sdk.TransferClient`
    """
    auth = get_refresh_token_authorizer(force_reauth)['transfer.api.globus.org']
    return globus_sdk.TransferClient(auth)


def get_local_endpoint_id():
    """
    Get the endpoint ID of a local Globus Connect Personal endpoint.

    Returns
    -------
    endpoint_id : `str`
        The endpoint ID.

    Raises
    ------
    ConnectionError
        If no local endpoint can be detected a connection error is raised.

    """
    local_endpoint = globus_sdk.LocalGlobusConnectPersonal()
    endpoint_id = local_endpoint.endpoint_id

    if not endpoint_id:
        raise ConnectionError(
            "Can not find a local Globus Connect endpoint.")

    return endpoint_id


@ensure_globus_authorized
def get_endpoint_id(endpoint, tfr_client):
    """
    Resolve an endpoint description to an ID.

    If the endpoint description is not a endpoint ID The `endpoint search
    <https://docs.globus.org/api/transfer/endpoint_search/#endpoint_search>`__
    functionality of the Globus API will be used, so any endpoint search can be
    specified. One and only one result must be returned from the search or a
    `ValueError` will be raised, unless one of the results is an exact text
    match for the search string, when that result will be used.

    Parameters
    ----------
    endpoint : `str`
        A description of an endpoint.

    tfr_client : `globus_sdk.TransferClient`
        The transfer client to use to query the endpoint.

    """
    tr = None

    # If there is a space in the endpoint it's not an id
    if ' ' not in endpoint:
        try:
            tr = tfr_client.get_endpoint(endpoint)
            return endpoint
        except globus_sdk.TransferAPIError as e:
            if e.code != "EndpointNotFound":
                raise

    if not tr:
        tr = tfr_client.endpoint_search(endpoint)

    responses = tr.data

    if len(responses) > 1:
        display_names = [a['display_name'] for a in responses]
        # If we have one and only one exact display name match use that
        if display_names.count(endpoint) == 1:
            return responses[display_names.index(endpoint)]['id']
        raise ValueError(f"Multiple matches for endpoint '{endpoint}': {display_names}")

    elif len(responses) == 0:
        raise ValueError(f"No matches found for endpoint '{endpoint}'")

    return responses[0]['id']


@ensure_globus_authorized
def auto_activate_endpoint(endpoint_id, tfr_client):  # pragma: no cover
    """
    Perform activation of a Globus endpoint.

    Parameters
    ----------
    endpoint_id : `str`
        The uuid of the endpoint to activate.

    tfr_client : `globus_sdk.TransferClient`
        The transfer client to use for the activation.

    """
    activation = tfr_client.endpoint_get_activation_requirements(endpoint_id)
    needs_activation = bool(activation['DATA'])
    activated = activation['activated']
    if needs_activation and not activated:
        r = tfr_client.endpoint_autoactivate(endpoint_id)
        if r['code'] == "AutoActivationFailed":
            webbrowser.open(f"https://app.globus.org/file-manager?origin_id={endpoint_id}",
                            new=1)
            input("Press Return after completing activation in your webbrowser...")
            r = tfr_client.endpoint_autoactivate(endpoint_id)


@ensure_globus_authorized
def get_directory_listing(path, endpoint=None):
    """
    Retrieve a list of all files in the path.

    Parameters
    ----------
    path : `pathlib.Path` or `str`
        The path to list on the endpoint.

    endpoint : `str` or `None`
        The name or uuid of the endpoint to use or None to attempt to connect
        to a local endpoint.

    Returns
    -------
    listing : `tuple`
        A list of all the files.

    """
    path = pathlib.Path(path)

    endpoint_id = None
    if endpoint is None:
        endpoint_id = get_local_endpoint_id()

    # Set this up after attempting local endpoint discovery so that we fail on
    # local endpoint discovery before needing to login.
    tc = get_transfer_client()

    if endpoint_id is None:
        endpoint_id = get_endpoint_id(endpoint, tc)
        auto_activate_endpoint(endpoint_id, tc)

    response = tc.operation_ls(endpoint_id, path=path.as_posix())
    names = [r['name'] for r in response]

    return [path / n for n in names]
