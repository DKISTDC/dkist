"""
Utilities and Helpers for dealing with Globus.

These functions are internal, and unlikely to need to be called directly.
"""
from .auth import *
from .endpoints import *
from .transfer import *

DKIST_DATA_CENTRE_ENDPOINT_ID = '433a057f-5ca0-4949-9bb1-c994514d1258'  # DKIST Sim Data 2021-04
"""The Globus endpoint ID of the main DKIST globus endpoint."""

DKIST_DATA_CENTRE_DATASET_PATH = "/{bucket}/{primaryProposalId}/{datasetId}"
"""
The path template to a dataset on the main endpoint. Should only use keys from
the asdf metadata schema.
"""
