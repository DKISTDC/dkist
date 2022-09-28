"""
Functions for working with dataset inventory.
"""
from typing import Dict
from collections import defaultdict

__all__ = ['dehumanize_inventory', 'humanize_inventory', 'INVENTORY_KEY_MAP']


class DefaultMap(defaultdict):
    """
    A tweak of default dict where the default value is the key that's missing.
    """
    def __missing__(self, key):
        return key


INVENTORY_KEY_MAP: Dict[str, str] = DefaultMap(None, {
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
})


def path_format_keys():
    header_names, human_names = INVENTORY_KEY_MAP.keys(), INVENTORY_KEY_MAP.values()
    header_names = [f"{h}" for h in header_names]
    human_names = [f"{h}" for h in human_names]
    w = [max([len(str(h)) for h in header_names]), max([len(str(h)) for h in human_names])]

    table = "\n".join([f"{header:<{w[0]+1}}{human:<{w[1]+1}}" for header, human in zip(header_names, human_names)])
    table = f"{'':=<{w[0]}} {'':=<{w[1]}}\n" + table
    table = f"{'Metadata keyword':<{w[0]}} {'Path key':<{w[1]}}\n" + table
    table = f"{'':=<{w[0]}} {'':=<{w[1]}}\n" + table
    table = table + f"\n{'':=<{w[0]}} {'':=<{w[1]}}"

    return table


def humanize_inventory(inventory: Dict[str, str]) -> Dict[str, str]:
    """
    Convert an inventory dict to have human readable keys.
    """
    key_converter = DefaultMap(None, INVENTORY_KEY_MAP)
    humanized_inventory = {}
    for key, value in inventory.items():
        humanized_inventory[key_converter[key]] = value
    return humanized_inventory


def sanitize_inventory(inv):
    # Putting this here because of cirvular imports
    from ..net.client import DKISTQueryResponseTable as Table

    t = Table.from_results([inv], client=None)
    return t[0].response_block_map


def dehumanize_inventory(humanized_inventory: Dict[str, str]) -> Dict[str, str]:
    """
    Convert a human readable inventory dict back to the original keys.
    """
    key_converter = DefaultMap(None, {value: key for key, value in INVENTORY_KEY_MAP.items()})
    inventory = {}
    for key, value in humanized_inventory.items():
        inventory[key_converter[key]] = value
    return inventory
