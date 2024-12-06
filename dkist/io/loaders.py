"""
This file contains code to lazy-load arrays from FITS files. It is designed to
minimise (virtual) memory usage and the number of open files.
"""

import abc
from pathlib import Path

import numpy as np

from astropy.io import fits

from sunpy.util.decorators import add_common_docstring

from dkist import log

__all__ = ["AstropyFITSLoader", "BaseFITSLoader"]


common_parameters = """

    Parameters
    ----------
    fileuri: `str`
        The filename, either absolute, or if `basepath` is specified, relative to `basepath`.
    shape: `tuple`
        The shape of the array to be proxied.
    dtype: `numpy.dtype`
        The dtype of the resulting array
    target: `int`
        The HDU number to load the array from.
    array_container: `BaseStripedExternalArray`
        The parent object of this class, which builds the array from a sequence
        of these loaders.
"""


@add_common_docstring(append=common_parameters)
class BaseFITSLoader(metaclass=abc.ABCMeta):
    """
    Base FITS array proxy.

    This class implements the array-like API needed for dask to convert a FITS
    array into a dask array without loading the FITS file until data access
    time.
    """

    def __init__(self, fileuri, shape, dtype, target, basepath):
        self.fileuri = fileuri
        self.shape = shape
        self.dtype = dtype
        self.target = target
        self.basepath = basepath
        self.ndim = len(self.shape)
        self.size = np.prod(self.shape)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"<FITS array in {self.fileuri} shape: {self.shape} dtype: {self.dtype}>"

    @property
    def data(self):
        return self[:]

    @abc.abstractmethod
    def __getitem__(self, slc):
        pass

    @property
    def absolute_uri(self):
        """
        Construct a non-relative path to the file, using ``basepath`` if provided.
        """
        if self.basepath:
            return self.basepath / self.fileuri

        return Path(self.fileuri)


@add_common_docstring(append=common_parameters)
class AstropyFITSLoader(BaseFITSLoader):
    """
    Resolve an `~asdf.ExternalArrayReference` to a FITS file using `astropy.io.fits`.
    """

    def __getitem__(self, slc):
        if not self.absolute_uri.exists():
            log.debug("File %s does not exist.", self.absolute_uri)
            # Use np.broadcast_to to generate an array of the correct size, but
            # which only uses memory for one value.
            return np.broadcast_to(np.nan, self.shape) * np.nan

        with fits.open(self.absolute_uri,
                       memmap=False,  # memmap is redundant with dask and delayed loading
                       do_not_scale_image_data=True,  # don't scale as we shouldn't need to
                       mode="denywrite") as hdul:
            log.debug("Accessing slice %s from file %s", slc, self.absolute_uri)

            hdu = hdul[self.target]
            if hasattr(hdu, "section"):
                return hdu.section[slc]

            return hdu.data[slc]
