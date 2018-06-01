import astropy.units as u
from astropy.io import fits
from astropy.table import Table

import gwcs.coordinate_frames as cf


def headers_from_filenames(filenames, hdu=0):
    """
    A generator to get the headers from filenames.
    """
    return (fits.getheader(fname, hdu=hdu) for fname in filenames)


def validate_headers(headers):
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
    out_headers = []
    h0 = next(headers)
    out_headers.append(h0)

    t = Table(names=h0.keys())
    t.add_row(h0)

    for h in headers:
        t.add_row(h)
        out_headers.append(h)

    """
    Let's do roughly the minimal amount of verification here.
    """

    # For some keys all the values must be the same
    same_keys = ['NAXIS', 'DNAXIS']
    naxis_same_keys = ['NAXISn', 'CTYPEn', 'CRPIXn', 'CRVALn']
    dnaxis_same_keys = ['DNAXISn', 'DTYPEn', 'DPNAMEn', 'DWNAMEn']
    # Expand n in NAXIS keys
    for nsk in naxis_same_keys:
        for naxis in range(1, t['NAXIS'][0] + 1):
            same_keys.append(nsk.replace('n', naxis))
    # Expand n in DNAXIS keys
    for dsk in dnaxis_same_keys:
        for dnaxis in range(1, t['DNAXIS'][0] + 1):
            same_keys.append(nsk.replace('n', dnaxis))

    validate_t = t[same_keys]
    assert (validate_t == validate_t[0]).all()

    return out_headers


def build_pixel_frame(header):
    """
    Given a header, build the input
    `gwcs.coordinate_frames.CoordinateFrame` object describing the pixel frame.

    Parameters
    ----------

    header : `dict`
        A fits header.

    Returns
    -------

    pixel_frame : `gwcs.coordinate_frames.CoordinateFrame`
        The pixel frame.
    """
    axes_types = [header[f'DTYPE{n}'] for n in range(header['DNAXIS'], 0, -1)]

    return cf.CoordinateFrame(naxes=header['DNAXIS'],
                              axes_type=axes_types,
                              axes_order=range(header['DNAXIS']),
                              unit=[u.pixel]*header['DNAXIS'],
                              axes_names=[header[f'DPNAME{n}'] for n in range(header['DNAXIS'], 0, -1)],
                              name='pixel')


def gwcs_from_filenames(filenames, hdu=0):
    """
    Given an iterable of filenames, build a gwcs for the dataset.
    """

    # headers is an iterator
    headers = headers_from_filenames(filenames, hdu=hdu)

    # headers is a now list
    headers = validate_headers(headers)

    # Now we know the headers are consistent, a lot of parts only need the first one.
    header = headers[0]

    pixel_frame = build_pixel_frame(header)

    # The physical types of the axes
    # axes_types = [header[f'DTYPE{n}'] for n in range(header['DNAXIS'], 0, -1)]
