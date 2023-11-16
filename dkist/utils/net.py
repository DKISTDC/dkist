"Functions for working with the net submodule"
from ..net import attrs as dattrs

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
