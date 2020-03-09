"""
Functions and helpers relating to working with simulated data.
"""
import random
import string

from astropy.time import Time
from sunpy.time import parse_time

__all__ = ['generate_datset_inventory_from_headers']


def _gen_type(gen_type, max_int=1e6, max_float=1e6, len_str=30):
    if gen_type is bool:
        return bool(random.randint(0, 1))
    elif gen_type is int:
        return random.randint(0, max_int)
    elif gen_type is float:
        return random.random() * max_float
    elif gen_type is list:
        return [_gen_type(str)]
    elif gen_type is Time:
        return parse_time("now")
    elif gen_type is str:
        return ''.join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(len_str))
    else:
        raise ValueError("Type {} is not supported".format(gen_type))  # pragma: no cover


def generate_datset_inventory_from_headers(headers):
    """
    Generate a dummy dataset inventory from headers.

    .. note::
       This is just for test data, it should not be used on real data.

    Parameters
    ----------

    headers: `astropy.table.Table`
    asdf_name: `str`

    """
    schema = [
        ('asdf_object_key', str),
        ('browse_movie_object_key', str),
        ('browse_movie_url', str),
        ('bucket', str),
        ('contributing_experiment_ids', list),
        ('contributing_proposal_ids', list),
        ('dataset_id', str),
        ('dataset_inventory_id', int),
        ('dataset_size', int),
        ('end_time', Time),
        ('exposure_time', float),
        ('filter_wavelengths', list),
        ('frame_count', int),
        ('has_all_stokes', bool),
        ('instrument_name', str),
        ('observables', list),
        ('original_frame_count', int),
        ('primary_experiment_id', str),
        ('primary_proposal_id', str),
        ('quality_average_fried_parameter', float),
        ('quality_average_polarimetric_accuracy', float),
        ('recipe_id', int),
        ('recipe_instance_id', int),
        ('recipe_run_id', int),
        ('start_time', Time),
        # ('stokes_parameters', str),
        ('target_type', str),
        ('wavelength_max', float),
        ('wavelength_min', float)
    ]

    header_mapping = {
        'start_time': 'DATE-BGN',
        'end_time': 'DATE-END',
        'filter_wavelengths': 'WAVELNGTH'}

    constants = {
        'frame_count': len(headers),
        'bucket': 'data',
    }

    output = {}

    for key, ktype in schema:
        if key in header_mapping:
            hdict = dict(zip(headers.colnames, headers[0]))
            output[key] = ktype(hdict.get(header_mapping[key], _gen_type(ktype)))
        else:
            output[key] = _gen_type(ktype)

    output.update(constants)
    return output
