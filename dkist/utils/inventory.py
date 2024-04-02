"""
Functions for working with dataset inventory.
"""
import re
import string
from collections import defaultdict

from astropy.table import Table

__all__ = ["dehumanize_inventory", "humanize_inventory", "INVENTORY_KEY_MAP"]


class DefaultMap(defaultdict):
    """
    A tweak of default dict where the default value is the key that's missing.
    """
    def __missing__(self, key):
        return key


INVENTORY_KEY_MAP: dict[str, str] = DefaultMap(None, {
        "asdfObjectKey": "asdf Filename",
        "boundingBox": "Bounding Box",
        "browseMovieObjectKey": "Movie Filename",
        "browseMovieUrl": "Preview URL",
        "bucket": "Storage Bucket",
        "contributingExperimentIds": "Experiment IDs",
        "contributingProposalIds": "Proposal IDs",
        "createDate": "Creation Date",
        "datasetId": "Dataset ID",
        "datasetSize": "Dataset Size",
        "embargoEndDate": "Embargo End Date",
        "endTime": "End Time",
        "experimentDescription": "Experiment Description",
        "exposureTime": "Exposure Time",
        "filterWavelengths": "Filter Wavelengths",
        "frameCount": "Number of Frames",
        "hasAllStokes": "Full Stokes",
        "instrumentName": "Instrument",
        "isDownloadable": "Downloadable",
        "isEmbargoed": "Embargoed",
        "observables": "Observables",
        "originalFrameCount": "Level 0 Frame count",
        "primaryExperimentId": "Primary Experiment ID",
        "primaryProposalId": "Primary Proposal ID",
        "qualityAverageFriedParameter": "Average Fried Parameter",
        "qualityAveragePolarimetricAccuracy": "Average Polarimetric Accuracy",
        "recipeId": "Recipe ID",
        "recipeInstanceId": "Recipe Instance ID",
        "recipeRunId": "Recipe Run ID",
        "startTime": "Start Time",
        "stokesParameters": "Stokes Parameters",
        "targetTypes": "Target Types",
        "updateDate": "Last Updated",
        "wavelengthMax": "Wavelength Max",
        "wavelengthMin": "Wavelength Min",
        "hasSpectralAxis": "Has Spectral Axis",
        "hasTemporalAxis": "Has Temporal Axis",
        "averageDatasetSpectralSampling": "Average Spectral Sampling",
        "averageDatasetSpatialSampling": "Average Spatial Sampling",
        "averageDatasetTemporalSampling": "Average Temporal Sampling",
        "qualityReportObjectKey": "Quality Report Filename",
        "inputDatasetParametersPartId": "Input Dataset Parameters Part ID",
        "inputDatasetObserveFramesPartId": "Input Dataset Observe Frames Part ID",
        "inputDatasetCalibrationFramesPartId": "Input Dataset Calibration Frames Part ID",
        "highLevelSoftwareVersion": "Summit Software Version",
        "workflowName": "Calibration Workflow Name",
        "workflowVersion": "Calibration Workflow Version",
        "headerDataUnitCreationDate": "HDU Creation Date",
        "observingProgramExecutionId": "Observing Program Execution ID",
        "instrumentProgramExecutionId": "Instrument Program Execution ID",
        "headerVersion": "Header Specification Version",
        "headerDocumentationUrl": "Header Documentation URL",
        "infoUrl": "Info URL",
        "calibrationDocumentationUrl": "Calibration Documentation URL"
})


def _key_clean(key):
    key = re.sub("[%s]" % re.escape(string.punctuation), "_", key)
    key = key.replace(" ", "_")
    key = "".join(char for char in key
                    if char.isidentifier() or char.isnumeric())
    return key.lower()


def path_format_keys(keymap):
    """
    Return a list of all valid keys for path formatting.
    """
    return tuple(map(_key_clean, keymap.values()))


def _path_format_table(keymap=INVENTORY_KEY_MAP):
    t = Table({"Inventory Keyword": list(keymap.keys()), "Path Key": path_format_keys(keymap)})
    return "\n".join(t.pformat(max_lines=-1, html=True))


def humanize_inventory(inventory: dict[str, str]) -> dict[str, str]:
    """
    Convert an inventory dict to have human readable keys.
    """
    key_converter = DefaultMap(None, INVENTORY_KEY_MAP)
    humanized_inventory = {}
    for key, value in inventory.items():
        humanized_inventory[key_converter[key]] = value
    return humanized_inventory


def path_format_inventory(human_inv):
    """
    Given a single humanized inventory record return a dict for formatting paths.
    """
    # Putting this here because of circular imports
    from dkist.net.client import DKISTQueryResponseTable as Table

    t = Table.from_results([{"searchResults": [human_inv]}], client=None)
    return t[0].response_block_map


def dehumanize_inventory(humanized_inventory: dict[str, str]) -> dict[str, str]:
    """
    Convert a human readable inventory dict back to the original keys.
    """
    key_converter = DefaultMap(None, {value: key for key, value in INVENTORY_KEY_MAP.items()})
    inventory = {}
    for key, value in humanized_inventory.items():
        inventory[key_converter[key]] = value
    return inventory
