"""
Helper functions for parsing files and processing headers.
"""

import numpy as np

from astropy.io import fits
from astropy.table import Table

__all__ = ['preprocess_headers', 'make_sorted_table', 'validate_headers',
           'table_from_headers', 'headers_from_filenames']


def headers_from_filenames(filenames, hdu=0):
    """
    Generator to get the headers from filenames.
    """
    return [dict(fits.getheader(fname, ext=hdu)) for fname in filenames]


def table_from_headers(headers):
    return Table(rows=headers, names=list(headers[0].keys()))


def validate_headers(table_headers):
    """
    Given a bunch of headers, validate that they form a coherent set. This
    function also adds the headers to a list as they are read from the file.

    Parameters
    ----------

    headers :  iterator
        An iterator of headers.

    Returns
    -------
    out_headers : `list`
        A list of headers.
    """
    t = table_headers

    """
    Let's do roughly the minimal amount of verification here.
    """

    # For some keys all the values must be the same
    same_keys = ['NAXIS', 'DNAXIS']
    naxis_same_keys = ['NAXISn', 'CTYPEn', 'CRVALn']  # 'CRPIXn'
    dnaxis_same_keys = ['DNAXISn', 'DTYPEn', 'DPNAMEn', 'DWNAMEn']
    # Expand n in NAXIS keys
    for nsk in naxis_same_keys:
        for naxis in range(1, t['NAXIS'][0] + 1):
            same_keys.append(nsk.replace('n', str(naxis)))
    # Expand n in DNAXIS keys
    for dsk in dnaxis_same_keys:
        for dnaxis in range(1, t['DNAXIS'][0] + 1):
            same_keys.append(dsk.replace('n', str(dnaxis)))

    validate_t = t[same_keys]

    for col in validate_t.columns.values():
        if not all(col == col[0]):
            raise ValueError(f"The {col.name} values did not all match:\n {col}")

    return table_headers


def make_sorted_table(headers, filenames):
    """
    Return an `astropy.table.Table` instance where the rows are correctly sorted.
    """
    theaders = table_from_headers(headers)
    theaders['filenames'] = filenames
    theaders['headers'] = headers
    dataset_axes = headers[0]['DNAXIS']
    array_axes = headers[0]['DAAXES']
    keys = [f'DINDEX{k}' for k in range(dataset_axes, array_axes, -1)]
    t = np.array(theaders[keys])
    return theaders[np.argsort(t, order=keys)]


def preprocess_headers(headers, filenames):
    table_headers = make_sorted_table(headers, filenames)

    validate_headers(table_headers)

    # Sort the filenames into DS order.
    sorted_filenames = np.array(table_headers['filenames'])
    sorted_headers = np.array(table_headers['headers'])

    table_headers.remove_columns(["headers", "filenames"])

    return table_headers, sorted_filenames, sorted_headers
