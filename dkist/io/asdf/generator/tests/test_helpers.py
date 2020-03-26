import os

import numpy as np
import pytest

import astropy.units as u
import gwcs.coordinate_frames as cf
from astropy.table import Table

from dkist.io.asdf.generator.generator import references_from_filenames
from dkist.io.asdf.generator.helpers import (_get_unique, _inventory_from_headers,
                                             _inventory_from_wcs, extract_inventory,
                                             headers_from_filenames)


def test_references_from_filesnames_shape_error(header_filenames):
    headers = headers_from_filenames(header_filenames, hdu=0)
    with pytest.raises(ValueError) as exc:
        references_from_filenames(header_filenames, headers, [2, 3])

        assert "incorrect number" in str(exc)
        assert "2, 3" in str(exc)
        assert str(len(header_filenames)) in str(exc)


def test_references_from_filenames(header_filenames):
    headers = headers_from_filenames(header_filenames, hdu=0)
    base = os.path.split(header_filenames[0])[0]
    refs = references_from_filenames(header_filenames, np.array(headers, dtype=object),
                                     (len(header_filenames),), relative_to=base)

    for ref in refs.fileuris:
        assert base not in ref


@pytest.fixture
def headers_inventory_214():
    """A minimal collection of headers to test inventory creation."""  # noqa
    return Table({
        'LINEWAV': [550, 550, 550],
        'FPA_EXPO': [10, 20, 30],
        'INSTRUME': ["VBI", "VBI", "VBI"],
        'FRIEDVAL': [1, 2, 3],
        'POL_ACC': [500, 500, 500],
        'RECIPEID': [10, 10, 10],
        'RINSTID': [20, 20, 20],
        'RRUNID': [30, 30, 30],
        'OBJECT': ["A", "B", "C"],
        'FRAMEVOL': [100, 120, 130],
        'EXPERID': ["00", "00", "00"],
        'EXPERID01': ["10", "10", "10"],
        'EXPERID02': ["20", "20", "20"],
        'PROPID': ["001", "001", "001"],
        'PROPID01': ["30", "30", "30"]
    })


def test_valid_inventory(headers_inventory_214):
    inv = _inventory_from_headers(headers_inventory_214)
    assert isinstance(inv, dict)

    assert inv["wavelength_min"] == inv["wavelength_max"] == 550
    assert inv["filter_wavelengths"] == [550]
    assert inv["instrument_name"] == "VBI"
    assert inv["observables"] == []
    assert inv["quality_average_fried_parameter"] == np.mean([1, 2, 3])
    assert inv["quality_average_polarimetric_accuracy"] == 500
    assert inv["recipe_id"] == 10
    assert inv["recipe_instance_id"] == 20
    assert inv["recipe_run_id"] == 30
    assert set(inv["target_type"]) == {"A", "B", "C"}
    assert inv["primary_proposal_id"] == "001"
    assert inv["primary_experiment_id"] == "00"
    assert set(inv["contributing_experiment_ids"]) == {"10", "20", "00"}
    assert set(inv["contributing_proposal_ids"]) == {"30", "001"}


def test_inventory_from_wcs(identity_gwcs_4d):
    inv = _inventory_from_wcs(identity_gwcs_4d)
    time_frame = list(filter(lambda x: isinstance(x, cf.TemporalFrame),
                             identity_gwcs_4d.output_frame.frames))[0]
    shape = identity_gwcs_4d.array_shape

    # This test transform is just 0 - n_pixel in all dimensions
    assert inv["wavelength_min"] == 0
    assert inv["wavelength_max"] == shape[2] - 1
    assert inv["bounding_box"] == ((0, 0), (shape[0] - 1, shape[1] - 1))
    assert inv["start_time"] == time_frame.reference_frame
    assert inv["end_time"] == (time_frame.reference_frame + (shape[3] - 1) * u.s)
    assert inv["stokes_parameters"] == ["I"]
    assert inv["has_all_stokes"] is False


def test_inventory_from_wcs_stokes(identity_gwcs_5d_stokes):
    inv = _inventory_from_wcs(identity_gwcs_5d_stokes)
    time_frame = list(filter(lambda x: isinstance(x, cf.TemporalFrame),
                             identity_gwcs_5d_stokes.output_frame.frames))[0]
    shape = identity_gwcs_5d_stokes.array_shape

    # This test transform is just 0 - n_pixel in all dimensions
    assert inv["wavelength_min"] == 0
    assert inv["wavelength_max"] == shape[2] - 1
    assert inv["bounding_box"] == ((0, 0), (shape[0] - 1, shape[1] - 1))
    assert inv["start_time"] == time_frame.reference_frame
    assert inv["end_time"] == (time_frame.reference_frame + (shape[3] - 1) * u.s)
    assert inv["stokes_parameters"] == ["I", "Q", "U", "V"]
    assert inv["has_all_stokes"] is True


def test_inventory_from_wcs_2d(identity_gwcs_3d_temporal):
    inv = _inventory_from_wcs(identity_gwcs_3d_temporal)
    time_frame = list(filter(lambda x: isinstance(x, cf.TemporalFrame),
                             identity_gwcs_3d_temporal.output_frame.frames))[0]
    shape = identity_gwcs_3d_temporal.array_shape

    # This test transform is just 0 - n_pixel in all dimensions
    assert "wavelength_min" not in inv
    assert "wavelength_max" not in inv
    assert inv["bounding_box"] == ((0, 0), (shape[0] - 1, shape[1] - 1))
    assert inv["start_time"] == time_frame.reference_frame
    assert inv["end_time"] == (time_frame.reference_frame + (shape[2] - 1) * u.s)
    assert inv["stokes_parameters"] == ["I"]
    assert inv["has_all_stokes"] is False


def test_unique_error():
    with pytest.raises(ValueError):
        _get_unique([1, 2, 3], singular=True)

    assert _get_unique([1, 2, 3], singular=False)


def test_extract_inventory(headers_inventory_214, identity_gwcs_4d):
    inv = extract_inventory(headers_inventory_214, identity_gwcs_4d)

    time_frame = list(filter(lambda x: isinstance(x, cf.TemporalFrame),
                             identity_gwcs_4d.output_frame.frames))[0]
    shape = identity_gwcs_4d.array_shape

    # This test transform is just 0 - n_pixel in all dimensions
    assert inv["wavelength_min"] == 0
    assert inv["wavelength_max"] == shape[2] - 1
    assert inv["bounding_box"] == ((0, 0), (shape[0] - 1, shape[1] - 1))
    assert inv["start_time"] == time_frame.reference_frame
    assert inv["end_time"] == (time_frame.reference_frame + (shape[3] - 1) * u.s)
    assert inv["stokes_parameters"] == ["I"]
    assert inv["has_all_stokes"] is False
    assert inv["filter_wavelengths"] == [550]
    assert inv["instrument_name"] == "VBI"
    assert inv["observables"] == []
    assert inv["quality_average_fried_parameter"] == np.mean([1, 2, 3])
    assert inv["quality_average_polarimetric_accuracy"] == 500
    assert inv["recipe_id"] == 10
    assert inv["recipe_instance_id"] == 20
    assert inv["recipe_run_id"] == 30
    assert set(inv["target_type"]) == {"A", "B", "C"}
    assert inv["primary_proposal_id"] == "001"
    assert inv["primary_experiment_id"] == "00"
    assert set(inv["contributing_experiment_ids"]) == {"10", "20", "00"}
    assert set(inv["contributing_proposal_ids"]) == {"30", "001"}


def test_extract_inventory_no_wave(headers_inventory_214, identity_gwcs_3d_temporal):
    inv = extract_inventory(headers_inventory_214, identity_gwcs_3d_temporal)

    time_frame = list(filter(lambda x: isinstance(x, cf.TemporalFrame),
                             identity_gwcs_3d_temporal.output_frame.frames))[0]
    shape = identity_gwcs_3d_temporal.array_shape

    # This test transform is just 0 - n_pixel in all dimensions
    assert inv["bounding_box"] == ((0, 0), (shape[0] - 1, shape[1] - 1))
    assert inv["wavelength_min"] == inv["wavelength_max"] == 550
    assert inv["start_time"] == time_frame.reference_frame
    assert inv["end_time"] == (time_frame.reference_frame + (shape[2] - 1) * u.s)
    assert inv["stokes_parameters"] == ["I"]
    assert inv["has_all_stokes"] is False
    assert inv["filter_wavelengths"] == [550]
    assert inv["instrument_name"] == "VBI"
    assert inv["observables"] == []
    assert inv["quality_average_fried_parameter"] == np.mean([1, 2, 3])
    assert inv["quality_average_polarimetric_accuracy"] == 500
    assert inv["recipe_id"] == 10
    assert inv["recipe_instance_id"] == 20
    assert inv["recipe_run_id"] == 30
    assert set(inv["target_type"]) == {"A", "B", "C"}
    assert inv["primary_proposal_id"] == "001"
    assert inv["primary_experiment_id"] == "00"
    assert set(inv["contributing_experiment_ids"]) == {"10", "20", "00"}
    assert set(inv["contributing_proposal_ids"]) == {"30", "001"}
