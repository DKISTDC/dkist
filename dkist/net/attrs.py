from ._attrs import (BoundingBox, BrowseMovie, Dataset, Embargoed, EmbargoEndTime,
                     Experiment, ExposureTime, FriedParameter, Observable,
                     PolarimetricAccuracy, Proposal, Recipe, SpatialSampling,
                     SpectralSampling, TargetType, TemporalSampling, WavelengthBand)

# Trick the docs into thinking these attrs are defined in here.
for _a in (
    Dataset,
    WavelengthBand,
    Embargoed,
    Observable,
    Experiment,
    Proposal,
    TargetType,
    Recipe,
    FriedParameter,
    PolarimetricAccuracy,
    ExposureTime,
    EmbargoEndTime,
    BrowseMovie,
    BoundingBox,
    SpectralSampling,
    SpatialSampling,
    TemporalSampling,
):
    _a.__module__ = __name__

__all__ = [
    "Dataset",
    "WavelengthBand",
    "Embargoed",
    "Observable",
    "Experiment",
    "Proposal",
    "TargetType",
    "Recipe",
    "FriedParameter",
    "PolarimetricAccuracy",
    "ExposureTime",
    "EmbargoEndTime",
    "BrowseMovie",
    "BoundingBox",
    "SpectralSampling",
    "SpatialSampling",
    "TemporalSampling",
]
