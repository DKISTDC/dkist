"Functions for working with the net submodule"
import os
import json
import urllib
import logging
import datetime as dt
from pathlib import Path

from ..net import attrs as dattrs


def get_api_response_location():
    # Location of DKIST package installation
    dkist_data = Path(*Path(__file__).parts[:-2]) / 'data'
    # This is definitely not the best way to do this but I can't get pytest to mock this function
    # properly so here we are
    if os.environ.get('IS_TEST_ENV'):
        dkist_data = dkist_data / 'test'
    return dkist_data / 'api_search_values.json'


INVENTORY_ATTR_MAP = {
    "range": {
        "averageDatasetSpatialSampling": {"attr": dattrs.SpatialSampling,
                                          "desc": "The min/max allowable dataset spatial sampling."},
        "averageDatasetSpectralSampling": {"attr": dattrs.SpectralSampling,
                                          "desc": "The min/max allowable dataset spectral sampling (nm)."},
        "averageDatasetTemporalSampling": {"attr": dattrs.TemporalSampling,
                                           "desc": "The min/max allowable dataset temporal sampling."},
        "exposureTime": {"attr": dattrs.ExposureTime,
                         "desc": "The min/max allowable exposure time within a dataset, in milliseconds."},
        "qualityAverageFriedParameter": {"attr": dattrs.FriedParameter,
                                         "desc": "The min/max allowable value of the average Fried Parameter within a dataset, in meters."},
    },
    "categorical": {
        "targetTypes": {"attr": dattrs.TargetType,
                        "desc": "A list of target types that can be present within a dataset."},
        "workflowName": {"attr": dattrs.WorkflowName,
                         "desc": "Name of the workflow used to process the dataset."},
        "workflowVersion": {"attr": dattrs.WorkflowVersion,
                            "desc": "Version of the workflow used to process the dataset."},
        "headerVersion": {"attr": dattrs.HeaderVersion,
                          "desc": "Version of the header schema used in the dataset."},
        "highLevelSoftwareVersion": {"attr": dattrs.SummitSoftwareVersion,
                                     "desc": "Version of the High Level Software (HLS) used on the summit during data collection."},
    }
}


# Location of DKIST package installation
search_api_response = get_api_response_location()
update_search_values = False
# Threshold age at which to refresh search values
max_age = dt.timedelta(days=7).total_seconds()
if not os.environ.get('DKIST_SKIP_UPDATE_SEARCH_VALUES'): #pragma: no cover
    if not search_api_response.exists():
        update_search_values = True
    else:
        last_modified = dt.datetime.fromtimestamp(search_api_response.stat().st_mtime)
        now = dt.datetime.now()
        file_age = (now - last_modified).total_seconds()
        if file_age > max_age:
            update_search_values = True

if update_search_values:
    logging.info("Downloading valid search values")
    data = urllib.request.urlopen('https://api.dkistdc.nso.edu/datasets/v1/searchValues')
    with open(search_api_response, "w") as f:
        search_values = json.dump(json.loads(data.read()), f)

with open(search_api_response, "r") as f:
    search_values = json.load(f)

search_values = {param["parameterName"]: param["values"] for param in search_values["parameterValues"]}
