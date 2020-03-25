import os

import numpy as np
import pytest

from astropy.table import Table

from dkist.io.asdf.generator.generator import references_from_filenames
from dkist.io.asdf.generator.helpers import _inventory_from_headers, headers_from_filenames


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
