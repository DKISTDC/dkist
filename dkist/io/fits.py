"""
This file contains code to lazy-load arrays from FITS files. It is designed to
minimise (virtual) memory usage and the number of open files.
"""

import os
import abc

from astropy.io import fits

__all__ = ['BaseFITSLoader', 'AstropyFITSLoader']


class BaseFITSLoader(metaclass=abc.ABCMeta):

    def __init__(self, externalarray, basepath=None):
        self.fitsarray = externalarray
        self.basepath = basepath
        # Private cache
        self._array = None
        self._fits_header = None
        # These are needed for this object to be array-like
        self.shape = self.fitsarray.shape
        self.dtype = self.fitsarray.dtype

    def __repr__(self):
        # repr alone should not force loading of the data
        if self._array is None:
            return "<FITS array (unloaded) in {0} shape: {1} dtype: {2}>".format(
                self.fitsarray.fileuri, self.fitsarray.shape, self.fitsarray.dtype)
        return repr(self._array)

    def __str__(self):
        # str alone should not force loading of the data
        if self._array is None:
            return "<FITS array (unloaded) in {0} shape: {1} dtype: {2}>".format(
                self.fitsarray.fileuri, self.fitsarray.shape, self.fitsarray.dtype)
        return str(self._array)

    def __array__(self):
        return self.fits_array

    def __getitem__(self, slc):
        return self.fits_array[slc]

    @property
    def absolute_uri(self):
        if self.basepath:
            return os.path.join(self.basepath, self.fitsarray.fileuri)
        else:
            return self.fitsarray.fileuri

    @property
    def fits_header(self):
        if not self._fits_header:
            self._fits_header = self._read_fits_header()
        return self._fits_header

    @property
    def fits_array(self):
        """
        This method opens the FITS file and returns a reference to the desired
        array.
        """
        if self._array is None:
            self._array = self._read_fits_array()
        return self._array

    @abc.abstractmethod
    def _read_fits_header(self):
        """
        Read and return the FITS header.

        .. note::

            This method must not leave the file open.

        """

    @abc.abstractmethod
    def _read_fits_array(self):
        """
        Read and return a reference to the FITS array.

        .. note::

            If it works with the underlying library, reading the header into
            the cache while the file is open is worthwhile.
        """


class AstropyFITSLoader(BaseFITSLoader):
    """
    A class that resolves FITS references in a lazy way.
    """

    def _read_fits_array(self):
        with fits.open(self.absolute_uri, memmap=True, do_not_scale_image_data=False) as hdul:
            hdul.verify('fix')
            hdu = hdul[self.fitsarray.target]
            if not self._fits_header:
                self._fits_header = hdu.header
            return hdu.data

    def _read_fits_header(self):
        with fits.open(self.absolute_uri) as hdul:
            hdul.verify('fix')
            hdu = hdul[self.fitsarray.target]
            return hdu.header
