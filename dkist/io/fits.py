"""
This file contains code to lazy-load arrays from FITS files. It is designed to
minimise (virtual) memory usage and the number of open files.
"""

import abc

from astropy.io import fits


class BaseFITSLoader(metaclass=abc.ABCMeta):

    def __init__(self, externalarray):
        self.fitsarray = externalarray
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
                self.fitsarray.filename, self.fitsarray.shape, self.fitsarray.dtype)
        return repr(self._array)

    def __str__(self):
        # str alone should not force loading of the data
        if self._array is None:
            return "<FITS array (unloaded) in {0} shape: {1} dtype: {2}>".format(
                self.fitsarray.filename, self.fitsarray.shape, self.fitsarray.dtype)
        return str(self._array)

    def __array__(self):
        return self.fits_array

    def __getitem__(self, slc):
        return self.fits_array[slc]

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
        if not self._array:
            self._array = self._read_array()
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


class AstropyFITSLoader:
    """
    A class that resolves FITS references in a lazy way.
    """

    def _read_fits_array(self):
        with fits.open(self.fitsarray.filename, memmap=True) as hdul:
            hdul.verify('fix')
            hdu = hdul[self.fitsarray.hdu_index]
            if not self._fits_header:
                self._fits_header = hdu.header
            return hdu.data

    def _read_fits_header(self):
        with fits.open(self.fitsarray.filename) as hdul:
            hdul.verify('fix')
            hdu = hdul[self.fitsarray.hdu_index]
            return hdu.header
