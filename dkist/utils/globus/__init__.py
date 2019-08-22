"""
Utilities and Helpers for dealing with Globus.
"""
from .auth import *
from .endpoints import *
from .transfer import *

DKIST_DATA_CENTRE_ENDPOINT_ID = '5e534393-e5bc-4042-9fb9-14f1649b120c'
"""The Globus endpoint ID of the main DKIST globus endpoint."""

DKIST_DATA_CENTRE_DATASET_PATH = "/{bucket}/{dataset_id}"
"""
The path template to a dataset on the main endpoint. Should only use keys from
the asdf metadata schema.
"""
