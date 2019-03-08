import os

import numpy as np

import asdf
import astropy.units as u
from asdf.tags.core.external_reference import ExternalArrayReference
from astropy.io.fits.hdu.base import BITPIX2DTYPE
from astropy.modeling.models import (AffineTransformation2D, Linear1D, Multiply,
                                     Pix2Sky_TAN, RotateNative2Celestial, Shift)
from astropy.time import Time
from gwcs.lookup_table import LookupTable

__all__ = ['make_asdf', 'time_model_from_date_obs', 'linear_time_model', 'linear_spectral_model',
           'spatial_model_from_quantity', 'spatial_model_from_header', 'references_from_filenames']


def references_from_filenames(filenames, headers, array_shape, hdu_index=0, relative_to=None):
    """
    Given an array of paths to FITS files create a set of nested lists of
    `asdf.external_reference.ExternalArrayReference` objects with the same
    shape.

    Parameters
    ----------

    filenames : `numpy.ndarray`
        An array of filenames, in numpy order for the output array (i.e. ``.flat``)

    headers : `list`
        A list of headers for files

    array_shape : `tuple`
        The desired output shape of the reference array. (i.e the shape of the
        data minus the HDU dimensions.)

    hdu_index : `int` (optional, default 0)
        The index of the HDU to reference. (Zero indexed)

    relative_to : `str` (optional)
        If set convert the filenames to be relative to this path.
    """

    filenames = np.asanyarray(filenames)
    reference_array = np.empty(array_shape, dtype=object)
    if filenames.size != reference_array.size:
        raise ValueError(f"An incorrect number of filenames ({filenames.size})"
                         f" supplied for array_shape ({array_shape})")

    for i, (filepath, head) in enumerate(zip(filenames.flat, headers.flat)):
        dtype = BITPIX2DTYPE[head['BITPIX']]
        shape = tuple([int(head[f"NAXIS{a}"]) for a in range(head["NAXIS"], 0, -1)])

        # Convert paths to relative paths
        relative_path = filepath
        if relative_to:
            relative_path = os.path.relpath(filepath, str(relative_to))

        reference_array.flat[i] = ExternalArrayReference(
            relative_path, hdu_index, dtype, shape)

    return reference_array.tolist()


def spatial_model_from_header(header):
    """
    Given a FITS compliant header with CTYPEx,y as HPLN, HPLT return a
    `~astropy.modeling.CompositeModel` for the transform.

    This function finds the HPLN and HPLT keys in the header and returns a
    model in Lon, Lat order.
    """
    latind = None
    lonind = None
    for k, v in header.items():
        if isinstance(v, str) and "HPLN" in v:
            lonind = int(k[5:])
        if isinstance(v, str) and "HPLT" in v:
            latind = int(k[5:])

    if latind is None or lonind is None:
        raise ValueError("Could not extract HPLN and HPLT from the header.")

    latproj = header[f'CTYPE{latind}'][5:]
    lonproj = header[f'CTYPE{lonind}'][5:]

    if latproj != lonproj:
        raise ValueError("The projection of the two spatial axes did not match.")  # pragma: no cover

    cunit1, cunit2 = u.Unit(header[f'CUNIT{lonind}']), u.Unit(header[f'CUNIT{latind}'])
    crpix1, crpix2 = header[f'CRPIX{lonind}'] * u.pix, header[f'CRPIX{latind}'] * u.pix
    crval1, crval2 = (header[f'CRVAL{lonind}'] * cunit1, header[f'CRVAL{latind}'] * cunit2)
    cdelt1, cdelt2 = (header[f'CDELT{lonind}'] * (cunit1 / u.pix),
                      header[f'CDELT{latind}'] * (cunit2 / u.pix))
    pc = np.matrix([[header[f'PC{lonind}_{lonind}'], header[f'PC{lonind}_{latind}']],
                    [header[f'PC{latind}_{lonind}'], header[f'PC{latind}_{latind}']]]) * cunit1

    return spatial_model_from_quantity(crpix1, crpix2, cdelt1, cdelt2, pc, crval1, crval2,
                                       projection=latproj)


def spatial_model_from_quantity(crpix1, crpix2, cdelt1, cdelt2, pc, crval1, crval2,
                                projection='TAN'):
    """
    Given quantity representations of a HPLx FITS WCS return a model for the
    spatial transform.

    The ordering of ctype1 and ctype2 should be LON, LAT
    """

    # TODO: Find this from somewhere else or extend it or something
    projections = {'TAN': Pix2Sky_TAN()}

    shiftu = Shift(-crpix1) & Shift(-crpix2)
    scale = Multiply(cdelt1) & Multiply(cdelt2)
    rotu = AffineTransformation2D(pc, translation=(0, 0)*u.arcsec)
    tanu = projections[projection]
    skyrotu = RotateNative2Celestial(crval1, crval2, 180*u.deg)
    return shiftu | scale | rotu | tanu | skyrotu


@u.quantity_input
def linear_spectral_model(spectral_width: u.nm, reference_val: u.nm):
    """
    A linear model in a spectral dimension. The reference pixel is always 0.
    """
    return Linear1D(slope=spectral_width/(1*u.pix), intercept=reference_val)


@u.quantity_input
def linear_time_model(cadence: u.s, reference_val: u.s = 0*u.s):
    """
    A linear model in a temporal dimension. The reference pixel is always 0.
    """
    if not reference_val:
        reference_val = 0 * cadence.unit
    return Linear1D(slope=cadence/(1*u.pix), intercept=reference_val)


def time_model_from_date_obs(date_obs, date_bgn=None):
    """
    Return a time model that best fits a list of dateobs's.
    """
    if not date_bgn:
        date_bgn = date_obs[0]
    date_obs = Time(date_obs)
    date_bgn = Time(date_bgn)

    deltas = date_bgn - date_obs

    # Work out if we have a uniform delta (i.e. a linear model)
    ddelta = (deltas.to(u.s)[:-1] - deltas.to(u.s)[1:])

    # If the length of the axis is one, then return a very simple model
    if ddelta.size == 0:
        return linear_time_model(cadence=0*u.s, reference_val=0*u.s)
    elif u.allclose(ddelta[0], ddelta):
        slope = ddelta[0]
        intercept = 0 * u.s
        return linear_time_model(cadence=slope, reference_val=intercept)
    else:
        print(f"creating tabular temporal axis. ddeltas: {ddelta}")
        return LookupTable(deltas.to(u.s))


def spectral_model_from_framewave(framewav):
    """
    Construct a linear or lookup table model for wavelength based on the
    framewav keys.
    """
    framewav = u.Quantity(framewav, unit=u.nm)
    wave_bgn = framewav[0]

    deltas = wave_bgn - framewav
    ddeltas = (deltas[:-1] - deltas[1:])
    # If the length of the axis is one, then return a very simple model
    if ddeltas.size == 0:
        return linear_spectral_model(0*u.nm, wave_bgn)
    if u.allclose(ddeltas[0], ddeltas):
        slope = ddeltas[0]
        return linear_spectral_model(slope, wave_bgn)
    else:
        print(f"creating tabular wavelength axis. ddeltas: {ddeltas}")
        return LookupTable(framewav)


def make_asdf(filename, *, dataset, gwcs, **kwargs):
    """
    Save an asdf file.

    All keyword arguments become keys in the top level of the asdf tree.
    """
    tree = {
        'wcs': gwcs,
        'data': dataset,
        **kwargs
    }

    with asdf.AsdfFile(tree) as ff:
        ff.write_to(filename)

    return filename
