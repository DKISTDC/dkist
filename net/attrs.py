"""
Search attrs for DKIST data.
"""
import astropy.units as u
from sunpy.net.attr import Attr as _Attr
from sunpy.net.attr import Range as _Range
from sunpy.net.attr import SimpleAttr as _SimpleAttr
from sunpy.net.attr import Time as _Time
from sunpy.net.vso.attrs import Physobs, Provider

__all__ = ['Provider', 'Physobs']


# Trick the docs into thinking these belong here.
for attr in [Provider, Physobs]:
    attr.__module__ = __name__


# _SimpleAttrs

class Dataset(_SimpleAttr):
    """
    Search for a dataset id.
    """
    def __init__(self, dataset_id):
        super().__init__(dataset_id)


class WavelengthBand(_SimpleAttr):
    """
    """
    def __init__(self, wavelength_band):
        super().__init__(wavelength_band)


class Embargoed(_SimpleAttr):
    """
    Search only for datasets with either are or are not under embargo.
    """
    def __init__(self, is_embargoed):
        super().__init__(is_embargoed)


class Observable(_SimpleAttr):
    """
    """
    def __init__(self, observable):
        super().__init__(observable)


class Experiment(_SimpleAttr):
    """
    """
    def __init__(self, experiment_id):
        super().__init__(self, experiment_id)


class Proposal(_SimpleAttr):
    """
    """
    def __init__(self, proposal_id):
        super().__init__(self, proposal_id)


class TargetType(_SimpleAttr):
    """
    """
    def __init__(self, target_type):
        super().__init__(self, target_type)


class Recipe(_SimpleAttr):
    """
    """
    def __init__(self, recipe_id):
        super().__init__(self, recipe_id)


class RecipeInstance(_SimpleAttr):
    """
    """
    def __init__(self, recipe_instance_id):
        super().__init__(self, recipe_instance_id)


# Range Attrs


class FriedParameter(_Range):
    """
    """


class PolarimetricAccuracy(_Range):
    """
    """


class ExposureTime(_Range):
    """
    """
    @u.quantity_input
    def __init__(self, expmin: u.s, expmax: u.s):
        super().__init__(expmin, expmax)


class CreationTime(_Time):
    """
    """

class EmbargoEndTime(_Time):
    """
    """


# Custom Attrs


class BrowseMovie(_Attr):
    """
    """
    def __init__(self, *, movieurl=None, movieobjectkey=None):
        if movieurl is None and movieobjectkey is None:
            raise ValueError("Either movieurl or movieobjectkey must be specified")
        self.movieurl = movieurl
        self.movieobjectkey = movieobjectkey


class BoundingBox(_Attr):
    """
    """
    def __init__(self, bottom_left, *, top_right=None, width=None, height=None):
        pass
