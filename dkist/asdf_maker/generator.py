from astropy.io import fits
from astropy.table import Table

__all__ = []


def headers_from_filenames(filenames, hdu=0):
    """
    A generator to get the headers from filenames.
    """
    return (fits.getheader(fname, hdu=hdu) for fname in filenames)


def validate_headers(headers):
    """
    Given a bunch of headers, validate that they form a coherent set.

    Parameters
    ----------

    headers :  iterator
        An iterator of headers.
    """
    h0 = next(headers)

    t = Table(names=h0.keys())
    t.add_row(h0)

    for h in headers:
        t.add_row(h)

    return headers


def gwcs_from_filenames(filenames, hdu=0):
    """
    Given an iterable of filenames, build a gwcs for the dataset.
    """

    headers = headers_from_filenames(filenames, hdu=hdu)

    headers = validate_headers(headers)
