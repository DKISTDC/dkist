"""
Search attrs for DKIST data.
"""
import astropy.units as u
import sunpy.net._attrs as _sunpy_attrs
from sunpy.net.attr import DataAttr as _DataAttr
from sunpy.net.attr import Range as _Range
from sunpy.net.attr import SimpleAttr as _SimpleAttr
from sunpy.net.vso.attrs import Provider

__all__ = ['Dataset', 'WavelengthBand', 'Embargoed', 'Observable',
           'Experiment', 'Proposal', 'TargetType', 'Recipe',
           'FriedParameter', 'PolarimetricAccuracy', 'ExposureTime',
           'EmbargoEndTime', 'BrowseMovie', 'BoundingBox', 'Provider']


# The attrs we are using from VSO should appear like they are defined in this
# module for documentation purposes. These should really be moved in sunpy from
# a.vso. to a.?
for attr in [Provider]:
    attr.__module__ = __name__


# SimpleAttrs

# datasetIds [array]
class Dataset(_SimpleAttr):
    """
    Unique identifier for a dataset.

    Parameters
    ----------
    dataset_id : `str`
        A random unique identifier for a dataset.
    """
    def __init__(self, dataset_id: str):
        super().__init__(dataset_id)


# filterWavelengths [array]
class WavelengthBand(_SimpleAttr):
    """
    Known wavelength feature present in dataset.

    Parameters
    ----------
    wavelength_band : `str`?
    """
    def __init__(self, wavelength_band: str):
        super().__init__(wavelength_band)


# observables [array]
class Observable(_SimpleAttr):
    """
    Unused at this time.
    """
    def __init__(self, observable: str):
        super().__init__(observable)


# primaryExperimentIds [array]
class Experiment(_SimpleAttr):
    """
    Unique identifier for a grouping of observations that meet the same scientific goal.

    ..note ::

        One `~dkist.net.attrs.Proposal` can consist of many
        `~dkist.net.attrs.Experiment` which can consist of many datasets.

    Parameters
    ----------
    experiment_id : `str`
        A unique identifier for an experiment.
    """
    def __init__(self, experiment_id: str):
        super().__init__(experiment_id)


# primaryProposalIds [array]
class Proposal(_SimpleAttr):
    """
    Unique identifier for a proposal.

    ..note ::

        One `~dkist.net.attrs.Proposal` can consist of many
        `~dkist.net.attrs.Experiment` which can consist of many datasets.

    Parameters
    ----------
    proposal_id : `str`
        A unique identifier for a proposal.
    """
    def __init__(self, proposal_id: str):
        super().__init__(proposal_id)


# targetTypes [array]
class TargetType(_SimpleAttr):
    """
    Name for the object observed by a dataset.

    Parameters
    ----------
    target_type: `str`
        A controlled string describing the target object.
    """
    def __init__(self, target_type: str):
        super().__init__(target_type)


# recipeId [array]
class Recipe(_SimpleAttr):
    """
    Unique identifier for a calibration pipeline.

    Parameters
    ----------
    recipe_id: `str`
        A unique identifier for the calibration pipeline.
    """
    def __init__(self, recipe_id: str):
        super().__init__(recipe_id)


# isEmbargoed
class Embargoed(_SimpleAttr):
    """
    Current embargo status of a dataset.

    Parameters
    ----------
    is_embargoed: `bool`
        A boolean determining if a dataset currently under embargo.
    """
    def __init__(self, is_embargoed: bool):
        super().__init__(bool(is_embargoed))


# Range Attrs


# qualityAverageFriedParameterMin, qualityAverageFriedParameterMax
class FriedParameter(_Range):
    """
    The average Fried parameter of a dataset.

    Parameters
    ----------
    friedmin : `u.Quantity`
        The minimum value of the average fried parameter to search between.

    friedmax : `u.Quantity`
        The maximum value of the average fried parameter to search between.
    """
    def __init__(self, friedmin: u.cm, friedmax: u.cm):
        super().__init__(friedmin, friedmax)

    def collides(self, other):
        return isinstance(other, self.__class__)


# qualityAveragePolarimetricAccuracyMin, qualityAverageFriedParameterMax
class PolarimetricAccuracy(_Range):
    """
    The average polarimetric accuracy of a dataset.

    Parameters
    ----------
    friedmin : `u.Quantity`
        The minimum value of the average fried parameter to search between.

    friedmax : `u.Quantity`
        The maximum value of the average fried parameter to search between.
    """

    def collides(self, other):
        return isinstance(other, self.__class__)


# exposureTimeMin, exposureTimeMax
class ExposureTime(_Range):
    """
    Most common exposure time of the calibrated data frames within the dataset.
    """
    @u.quantity_input
    def __init__(self, expmin: u.s, expmax: u.s):
        super().__init__(expmin, expmax)

    def collides(self, other):
        return isinstance(other, self.__class__)


# embargoEndDateMin, embargoEndDateMax
class EmbargoEndTime(_sunpy_attrs.Time):
    """
    The time at which an embargo on the dataset lapses.
    """


# Custom Attrs


# browseMovieUrl & browseMovieObjectKey
class BrowseMovie(_DataAttr):
    """
    The identifier for a browse move associated with a dataset.
    """
    def __init__(self, *, movieurl: str = None, movieobjectkey: str = None):
        if movieurl is None and movieobjectkey is None:
            raise ValueError("Either movieurl or movieobjectkey must be specified")
        self.movieurl = movieurl
        self.movieobjectkey = movieobjectkey

    def collides(self, other):
        return isinstance(other, self.__class__)


# rectangleContainedByBoundingBox, rectangleContainingBoundingBox, rectangleIntersectingBoundingBox
class BoundingBox(_DataAttr):
    """
    The dataset bounding box in spatial coordinates.
    """
    def __init__(self, bottom_left, *, top_right=None, width=None, height=None, search="containing"):
        pass

    def collides(self, other):
        return isinstance(other, self.__class__)
