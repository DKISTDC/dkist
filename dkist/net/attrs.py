"""
Search attributes which are specific to the `dkist.net.DKISTDatasetClient`.

Other attributes provided by `sunpy.net.attrs` are supported by the client.
"""
import astropy.units as u
import sunpy.net._attrs as _sunpy_attrs
from sunpy.coordinates.frames import Helioprojective
from sunpy.coordinates.utils import get_rectangle_coordinates
from sunpy.net.attr import DataAttr as _DataAttr
from sunpy.net.attr import Range as _Range
from sunpy.net.attr import SimpleAttr as _SimpleAttr

__all__ = ['Dataset', 'WavelengthBand', 'Embargoed', 'Observable',
           'Experiment', 'Proposal', 'TargetType', 'Recipe',
           'FriedParameter', 'PolarimetricAccuracy', 'ExposureTime',
           'EmbargoEndTime', 'BrowseMovie', 'BoundingBox',
           'SpectralSampling', 'SpatialSampling', 'TemporalSampling']


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

    .. note::

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

    .. note::

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

    Parameters
    ----------
    bottom_left : `~astropy.coordinates.BaseCoordinateFrame` or `~astropy.coordinates.SkyCoord`
        The bottom-left coordinate of the rectangle.
        Supports passing both the bottom left and top right coordinates by passing with a shape of ``(2,)``.
    top_right : `~astropy.coordinates.BaseCoordinateFrame` or `~astropy.coordinates.SkyCoord`, optional
        The top-right coordinate of the rectangle.
        If in a different frame than ``bottom_left`` and all required metadata for frame conversion is present,
        ``top_right`` will be transformed to ``bottom_left`` frame.
    width : `~astropy.units.Quantity`, optional
        The width of the rectangle.
        Must be omitted if the coordinates of both corners have been specified.
    height : `~astropy.units.Quantity`, optional
        The height of the rectangle.
        Must be omitted if the coordinates of both corners have been specified.
    search : {"containing", "contained", "intersecting"}, optional
        The type of search to perform, defaults to ``"containing"``. A
        "containing" search, is where the specified search box fully contains
        the dataset bounding box, a "contained" search is where the specified
        search box is fully contained by the dataset bounding box and
        "intersecting" is where there is any intersection of the search and
        dataset boxes.

    Notes
    -----
    The dataset search is performed only with the latitude and longitude
    coordinate in helioprojective coordinates at the observatory at the time of
    the observation. This search API is not designed to provide the ability to
    search based on fully specified coordinate frames, however, if used
    correctly the SunPy coordinate transformations can be used to do limited
    searches in other frames.
    The coordinates specified to this search attribute are converted to a
    helioprojective frame with Earth as the observer
    (``sunpy.coordinates.Helioprojective(observer="earth")``).
    Therefore any input which is convertible to this frame is acceptable.
    However, it is important to consider how these coordinates will be
    interpreted. The coordinates will not be interpreted **at the time of the
    observation**, they will be interpreted as an inertial point in space at
    the time specified when passed to this function. This means that if you for
    instance pass a heliographic coordinate to this attribute for Jan 1st
    2020, but you search for a dataset on Jan 1st 2025, it will use the
    helioprojective coordinate equivalent to the heliographic coordinate passed
    as seen by an observer on Earth **on Jan 1st 2020**.
    """

    def __init__(self, bottom_left, *, top_right=None, width: u.deg = None,
                 height: u.deg = None, search="containing"):
        bottom_left, top_right = get_rectangle_coordinates(bottom_left,
                                                           top_right=top_right,
                                                           width=width, height=height)
        bottom_left = bottom_left.transform_to(Helioprojective(observer="earth"))
        top_right = top_right.transform_to(Helioprojective(observer="earth"))

        self.hpc_bounding_box_arcsec = ((bottom_left.Tx.to_value(u.arcsec),
                                         bottom_left.Ty.to_value(u.arcsec)),
                                        (top_right.Tx.to_value(u.arcsec),
                                         top_right.Ty.to_value(u.arcsec)))

        self.search_type = search

    def collides(self, other):
        return isinstance(other, self.__class__)

# averageDatasetSpectralSamplingMin, averageDatasetSpectralSamplingMax
class SpectralSampling(_Range):
    """
    The average spectral sampling of a dataset.

    Parameters
    ----------
    spectralmin : `u.Quantity`
        The minimum value of the average spectral sampling to search between.

    spectralmax : `u.Quantity`
        The maximum value of the average spectral sampling to search between.
    """
    u.quantity_input(equivalencies=u.spectral())
    def __init__(self, spectralmin: u.nm, spectralmax: u.nm):
        super().__init__(spectralmin, spectralmax)

    def collides(self, other):
        return isinstance(other, self.__class__)

# averageDatasetSpatialSamplingMin, averageDatasetSpatialSamplingMax
class SpatialSampling(_Range):
    """
    The average spatial sampling of a dataset.

    Parameters
    ----------
    spatialmin :
        The minimum value of the average spatial sampling to search between.

    spatialmax :
        The maximum value of the average spatial sampling to search between.
    """
    def __init__(self, spatialmin: u.arcsec/u.pix, spatialmax: u.arcsec/u.pix):
        super().__init__(spatialmin, spatialmax)

    def collides(self, other):
        return isinstance(other, self.__class__)

# averageDatasetTemporalSamplingMin, averageDatasetTemporalSamplingMax
class TemporalSampling(_Range):
    """
    The average temporal sampling of a dataset.

    Parameters
    ----------
    temporalmin : `u.Quantity`
        The minimum value of the average temporal sampling to search between.

    temporalmax : `u.Quantity`
        The maximum value of the average temporal sampling to search between.
    """
    def __init__(self, temporalmin: u.s, temporalmax: u.s):
        super().__init__(temporalmin, temporalmax)

    def collides(self, other):
        return isinstance(other, self.__class__)
