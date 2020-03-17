"""
Helper functions for parsing files and processing headers.
"""

from functools import partial

import numpy as np
import scipy.stats

import astropy.units as u
import gwcs.coordinate_frames as cf
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.table import Table
from astropy.time import Time

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


def _inventory_from_wcs(wcs):
    """
    Parse the gWCS and extract any inventory keys needed.

    This assumes all WCSes have a celestial and temporal component.

    Keys for wavelength will not be added if there is no spectral component,
    stokes keys are always added (defaulting to just I if not in the WCS).
    """

    bottom_left_array = [0] * wcs.pixel_n_dim
    top_right_array = np.array(wcs.pixel_shape) - 1

    bottom_left_world = wcs.array_index_to_world(*bottom_left_array)
    top_right_world = wcs.array_index_to_world(*top_right_array)

    start_time = list(filter(lambda x: isinstance(x, Time), bottom_left_world))[0]
    end_time = list(filter(lambda x: isinstance(x, Time), top_right_world))[0]

    bottom_left_celestial = list(filter(lambda x: isinstance(x, SkyCoord), bottom_left_world))[0]
    top_right_celestial = list(filter(lambda x: isinstance(x, SkyCoord), top_right_world))[0]

    bounding_box = ((bottom_left_celestial.Tx.to_value(u.arcsec), bottom_left_celestial.Ty.to_value(u.arcsec)),
                    (top_right_celestial.Tx.to_value(u.arcsec), top_right_celestial.Tx.to_value(u.arcsec)))

    inventory = {'bounding_box': bounding_box,
                 'start_time': start_time.isot,
                 'end_time': end_time.isot}

    if not isinstance(wcs.output_frame, cf.CompositeFrame):
        raise TypeError("Can't parse this WCS as expected.")

    spec_frame = list(filter(lambda f: isinstance(f, cf.SpectralFrame), wcs.output_frame.frames))
    if spec_frame:
        spectral_axes = spec_frame[0].axes_order[0] - wcs.pixel_n_dim
        inventory["wavelength_min"] = bottom_left_world[spectral_axes].to_value(u.nm)
        inventory["wavelength_max"] = top_right_world[spectral_axes].to_value(u.nm)

    stokes_frame = list(filter(lambda f: isinstance(f, cf.StokesFrame), wcs.output_frame.frames))
    if stokes_frame:
        stokes_axes = stokes_frame[0].axes_order[0]
        pixel_coords = [0] * wcs.pixel_n_dim
        pixel_coords[stokes_axes] = (0, 1, 2, 3)
        all_stokes = wcs.pixel_to_world(*np.broadcast_arrays(*pixel_coords))
        stokes_components = all_stokes[stokes_axes - 1]

        inventory["stokes_parameters"] = list(map(str, stokes_components))
        inventory["has_all_stokes"] = len(stokes_components) > 1

    else:
        inventory["stokes_parameters"] = ['I']
        inventory["has_all_stokes"] = False

    return inventory


def _get_unique(column, singular=False):
    uniq = list(set(column))
    if singular:
        if len(uniq) == 1:
            return uniq[0]
        else:
            raise ValueError("Column does not result in a singular unique value")

    return uniq


def _get_number_apply(column, func):
    return func(column)


def _inventory_from_headers(headers):
    inventory = {}

    mode = partial(scipy.stats.mode, axis=None, nan_policy="raise")

    inventory["wavelength_min"] = inventory["wavelength_max"] = _get_unique(headers['LINEWAV'])[0]
    inventory["exposure_time"] = _get_number_apply(headers['FPA_EXPO'], mode)
    inventory["filter_wavelengths"] = _get_unique(headers['LINEWAV'])
    inventory["instrument_name"] = _get_unique(headers['INSTRUME'], singular=True)
    inventory["observables"] = [] # _get_unique(headers[''])
    inventory["quality_average_fried_parameter"] = _get_number_apply(headers['FRIEDVAL'], np.mean)
    inventory["quality_average_polarimetric_accuracy"] = _get_unique(headers[''], singular=True)
    inventory["recipe_id"] = _get_unique(headers['RECIPEID'], singular=True)
    inventory["recipe_instance_id"] = _get_unique(headers['RINSTID'], singular=True)
    inventory["recipe_run_id"] = _get_unique(headers['RRUNID'], singular=True)
    inventory["target_type"] = _get_unique(headers['OBJECT'])
    inventory["primary_experiment_id"] = _get_unique(headers['EXPER_ID'], singular=True)
    inventory["dataset_size"] = _get_number_apply(headers['FRAMEVOL'], np.sum)
    # inventory["contributing_experiment_ids"] = _get_keys_matching(headers, "EXPRID??")
    # inventory["contributing_proposal_ids"] =_get_keys_matching(headers, "PROPID??")

    return inventory


def extract_inventory(headers, wcs, **inventory):
    """
    Generate the inventory record for an asdf file from an asdf tree.

    Parameters
    ----------
    tree : `dict`
        The incomplete asdf tree. Needs to contain the dataset object.

    inventory : `dict`
        Additional inventory keys that can not be computed from the headers or the WCS.


    Returns
    -------

    tree: `dict`
        The updated tree with the inventory.

    """
    # The headers will populate passband info for VBI and then wcs will
    # override it if there is a wavelength axis in the dataset,
    # any supplied kwargs override things extracted from dataset.
    return {**_inventory_from_headers(headers), **_inventory_from_wcs(wcs), **inventory}
