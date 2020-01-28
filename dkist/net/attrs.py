"""
Search attrs for DKIST data.
"""
import astropy.units as u
import sunpy.net._attrs as _sunpy_attrs
from sunpy.net.attr import Attr as _Attr
from sunpy.net.attr import Range as _Range
from sunpy.net.attr import SimpleAttr as _SimpleAttr
from sunpy.net.vso.attrs import Physobs, Provider

__all__ = ['Dataset', 'WavelengthBand', 'Embargoed', 'Observable',
           'Experiment', 'Proposal', 'TargetType', 'Recipe', 'RecipeInstance',
           'FriedParameter', 'PolarimetricAccuracy', 'ExposureTime', 'CreationTime',
           'EmbargoEndTime', 'BrowseMovie', 'BoundingBox', 'Provider', 'Physobs']


_supported_core_attrs = [
    # startTime, endTime
    _sunpy_attrs.Time,
    # instrumentNames [array]
    _sunpy_attrs.Instrument,
    # wavelengthMin, wavelengthMax
    _sunpy_attrs.Wavelength,
    # Nothing
    _sunpy_attrs.Level]


# The attrs we are using from VSO should appear like they are defined in this
# module for documentation purposes. These should really be moved in sunpy core?
for attr in [Provider, Physobs]:
    attr.__module__ = __name__


# SimpleAttrs

# datasetIds [array]
class Dataset(_SimpleAttr):
    """
    Search for a dataset id.
    """
    def __init__(self, dataset_id):
        super().__init__(dataset_id)


# filterWavelengths [array]
class WavelengthBand(_SimpleAttr):
    """
    """
    def __init__(self, wavelength_band):
        super().__init__(wavelength_band)


# observables [array]
class Observable(_SimpleAttr):
    """
    """
    def __init__(self, observable):
        super().__init__(observable)


# primaryExperimentIds [array]
class Experiment(_SimpleAttr):
    """
    """
    def __init__(self, experiment_id):
        super().__init__(self, experiment_id)


# primaryProposalIds [array]
class Proposal(_SimpleAttr):
    """
    """
    def __init__(self, proposal_id):
        super().__init__(self, proposal_id)


# targetTypes [array]
class TargetType(_SimpleAttr):
    """
    """
    def __init__(self, target_type):
        super().__init__(self, target_type)


# recipeId [array]
class Recipe(_SimpleAttr):
    """
    """
    def __init__(self, recipe_id):
        super().__init__(self, recipe_id)


# recipeInstanceId [array]
class RecipeInstance(_SimpleAttr):
    """
    """
    def __init__(self, recipe_instance_id):
        super().__init__(self, recipe_instance_id)


# isEmbargoed
class Embargoed(_SimpleAttr):
    """
    Search only for datasets with either are or are not under embargo.
    """
    def __init__(self, is_embargoed):
        super().__init__(is_embargoed)


# Range Attrs


# qualityAverageFriedParameterMin, qualityAverageFriedParameterMax
class FriedParameter(_Range):
    """
    """


# qualityAveragePolarimetricAccuracyMin, qualityAverageFriedParameterMax
class PolarimetricAccuracy(_Range):
    """
    """


# exposureTimeMin, exposureTimeMax
class ExposureTime(_Range):
    """
    """
    @u.quantity_input
    def __init__(self, expmin: u.s, expmax: u.s):
        super().__init__(expmin, expmax)


# createDateMin, createDateMax
class CreationTime(_sunpy_attrs.Time):
    """
    """

# embargoEndDateMin, embargoEndDateMax
class EmbargoEndTime(_sunpy_attrs.Time):
    """
    """


# Custom Attrs


# browseMovieUrl & browseMovieObjectKey
class BrowseMovie(_Attr):
    """
    """
    def __init__(self, *, movieurl=None, movieobjectkey=None):
        if movieurl is None and movieobjectkey is None:
            raise ValueError("Either movieurl or movieobjectkey must be specified")
        self.movieurl = movieurl
        self.movieobjectkey = movieobjectkey


# rectangleContainedByBoundingBox, rectangleContainingBoundingBox, rectangleIntersectingBoundingBox
class BoundingBox(_Attr):
    """
    """
    def __init__(self, bottom_left, *, top_right=None, width=None, height=None, search="containing"):
        pass
