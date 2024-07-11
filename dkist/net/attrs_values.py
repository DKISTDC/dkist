"Functions for working with the net submodule"
import json
import urllib
import datetime as dt
import importlib.resources
from pathlib import Path

import platformdirs

from sunpy.net import attrs as sattrs  # noqa: ICN001

import dkist.data
from dkist import log
from dkist.net import attrs as dattrs
from dkist.net import conf as net_conf

__all__ = ["attempt_local_update", "get_search_attrs_values"]

# Map keys in dataset inventory to Fido attrs
INVENTORY_ATTR_MAP = {
    # Only categorical data are supported currently
    "categorical": {
        "instrumentNames": sattrs.Instrument,
        "targetTypes": dattrs.TargetType,
        "workflowName": dattrs.WorkflowName,
        "workflowVersion": dattrs.WorkflowVersion,
        "headerVersion": dattrs.HeaderVersion,
        "highLevelSoftwareVersion": dattrs.SummitSoftwareVersion,
    },
    "range": {
        "averageDatasetSpatialSampling": dattrs.SpatialSampling,
        "averageDatasetSpectralSampling": dattrs.SpectralSampling,
        "averageDatasetTemporalSampling": dattrs.TemporalSampling,
        "exposureTime": dattrs.ExposureTime,
        "qualityAverageFriedParameter": dattrs.FriedParameter,
    }
}


class UserCacheMissing(Exception):
    """
    An exception for when we have deleted the user cache.
    """


def _get_file_age(path: Path) -> dt.timedelta:
    last_modified = dt.datetime.fromtimestamp(path.stat().st_mtime)
    now = dt.datetime.now()
    return (now - last_modified)


def _get_cached_json() -> list[Path, bool]:
    """
    Return the path to a local copy of the JSON file, and if the file should be updated.

    If a user-local copy has been downloaded that will always be used.
    """
    package_file = importlib.resources.files(dkist.data) / "api_search_values.json"
    user_file = platformdirs.user_data_path("dkist") / "api_search_values.json"

    return_file = package_file
    if user_file_exists := user_file.exists():
        return_file = user_file

    update_needed = False
    if not user_file_exists:
        update_needed = True
    if user_file_exists and _get_file_age(return_file) > dt.timedelta(days=net_conf.attr_max_age):
        update_needed = True

    return return_file, update_needed


def _fetch_values(timeout: int = 1) -> bytes:
    """
    Make a request for new values.

    This is a separate function mostly for mocking it in the tests.
    """
    data = urllib.request.urlopen(
        net_conf.dataset_endpoint + net_conf.dataset_search_values_path, timeout=timeout
    )
    return data.read()


def attempt_local_update(*, timeout: int = 1, user_file: Path = None, silence_net_errors: bool = True) -> bool:
    """
    Attempt to update the local data copy of the values.

    Parameters
    ----------
    timeout
        The number of seconds to wait before timing out an update request. This
        is set low by default because this code is run at import of
        ``dkist.net``.
    user_file
        The file to save the updated attrs JSON to. If `None` platformdirs will
        be used to get the user data path.
    silence_net_errors
        If `True` catch all errors caused by downloading new values in this function.

    Returns
    -------
    success
        `True` if the update succeeded or `False` otherwise.
    """
    if user_file is None:
        user_file = platformdirs.user_data_path("dkist") / "api_search_values.json"
    user_file = Path(user_file)
    if not user_file.exists():
        user_file.parent.mkdir(exist_ok=True, parents=True)

    log.info(f"Fetching updated search values for the DKIST client to {user_file}")

    try:
        data = _fetch_values(timeout)
    except Exception as err:
        log.error("Failed to download new dkist attrs values. attr values for dkist may be outdated.")
        log.debug(str(err))
        if not silence_net_errors:
            raise
        return False

    try:
        # Save the data
        with open(user_file, "wb") as f:
            f.write(data)

        # Test that the file we just saved can be parsed as json
        with open(user_file) as f:
            json.load(f)

        return True

    except Exception as err:
        log.error("Downloaded file could not be saved or is not valid JSON, removing cached file.")
        user_file.unlink(missing_ok=True)
        raise UserCacheMissing from err


def get_search_attrs_values(*, allow_update: bool = True, timeout: int = 1) -> dict:
    """
    Return the search values, updating if needed.

    Parameters
    ----------
    allow_update
        Allow fetching updated values from the DKIST data center if they haven't
        been updated in the configured amount of time (7 days by default).
    timeout
        The number of seconds to wait before timing out an update request. This
        is set low by default because this code is run at import of
        ``dkist.net``.

    Returns
    -------
    attr_values
        Return a transformed version of the loaded attr values from the DKIST
        data center.
    """
    local_path, update_needed = _get_cached_json()
    if allow_update and update_needed:
        try:
            attempt_local_update(timeout=timeout)
        except UserCacheMissing:
            # if we have deleted the user cache we must use the file shipped with the package
            local_path = importlib.resources.files(dkist.data) / "api_search_values.json"

    if not update_needed:
        log.debug("No update to dkist attr values needed.")
        log.debug("Using dkist attr values from %s", local_path)

    with open(local_path) as f:
        search_values = json.load(f)

    search_values = {param["parameterName"]: param["values"] for param in search_values["parameterValues"]}

    attr_values = {}
    for key, attr in INVENTORY_ATTR_MAP["categorical"].items():
        attr_values[attr] = [(name, "") for name in search_values[key]["categoricalValues"]]

    for key, attr in INVENTORY_ATTR_MAP["range"].items():
        attr_values[attr] = [("all", f"Value between {search_values[key+'Min']['minValue']:.5f} and {search_values[key+'Max']['maxValue']:.5f}")]

    # Time - Time attr allows times in the full range but start and end time are given separately by the DKIST API
    attr_values[sattrs.Time] = [("time", f"Min: {search_values['startTimeMin']['minValue']} - Max: {search_values['endTimeMax']['maxValue']}.")]

    return attr_values
