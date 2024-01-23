"Functions for working with the net submodule"
import json
import urllib
import datetime as dt
import importlib.resources

import platformdirs

from sunpy.net import attrs as sattrs

import dkist.data
from dkist import log
from dkist.net import attrs as dattrs

__all__ = ["get_search_attrs_values"]

# TODO: This should be in the config file
# Threshold age at which to refresh search values
MAX_AGE = dt.timedelta(days=7).total_seconds()

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
}


def get_file_age(path):
    last_modified = dt.datetime.fromtimestamp(path.stat().st_mtime)
    now = dt.datetime.now()
    return (now - last_modified).total_seconds()


def get_cached_json():
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
    if not user_file_exists and get_file_age(return_file) > MAX_AGE:
        update_needed = True

    return return_file, update_needed


def fetch_values_to_file(filepath, *, timeout=1):
    # Import here to avoid unitialised module
    from dkist.net import conf as net_conf
    data = urllib.request.urlopen(
        net_conf.dataset_endpoint + net_conf.dataset_search_values_path, timeout=timeout
    )
    with open(filepath, "wb") as f:
        f.write(data.read())


def attempt_local_update(*, timeout=1):
    """
    Attempt to update the local data copy of the values.
    """
    user_file = platformdirs.user_data_path("dkist") / "api_search_values.json"
    user_file.parent.mkdir(exist_ok=True)

    log.info("Fetching updated search values for the DKIST client.")

    success = False
    try:
        fetch_values_to_file(user_file, timeout=timeout)
        success = True
    except Exception as err:
        log.error("Failed to download new attrs values.")
        log.debug(str(err))
        # If an error has occured then remove the local file so it isn't
        # corrupted or invalid.
        user_file.unlink()

    # Test that the file we just saved can be parsed as json
    try:
        with open(user_file, "r") as f:
            json.load(f)
    except Exception:
        user_file.unlink()
        return False

    return success


def get_search_attrs_values(*, allow_update=True, timeout=1):
    """
    Return the search values, updating if needed.
    """
    local_path, update_needed = get_cached_json()
    if allow_update and update_needed:
        attempt_local_update(timeout=timeout)
    if not update_needed:
        log.debug("No update to attr values needed.")
        log.debug(local_path.as_posix())

    with open(local_path, "r") as f:
        search_values = json.load(f)

    search_values = {param["parameterName"]: param["values"] for param in search_values["parameterValues"]}

    return_values = {}
    for key, attr in INVENTORY_ATTR_MAP["categorical"].items():
        return_values[attr] = [(name, "") for name in search_values[key]["categoricalValues"]]

    return return_values
