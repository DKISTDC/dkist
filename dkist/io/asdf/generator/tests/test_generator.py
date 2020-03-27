import pathlib

import pytest

import asdf

from dkist import Dataset
from dkist.dataset import Dataset
from dkist.io.asdf.generator.generator import (asdf_tree_from_filenames, dataset_from_fits,
                                               references_from_filenames)
from dkist.io.asdf.generator.helpers import (headers_from_filenames, preprocess_headers,
                                             table_from_headers, validate_headers)


def test_array_container_shape(header_filenames):

    headers = headers_from_filenames(header_filenames, hdu=0)
    table_headers, sorted_filenames, sorted_headers = preprocess_headers(headers, header_filenames)
    # Get the array shape
    shape = tuple((headers[0][f'DNAXIS{n}'] for n in range(headers[0]['DNAXIS'],
                                                           headers[0]['DAAXES'], -1)))
    # References from filenames
    array_container = references_from_filenames(sorted_filenames, sorted_headers, array_shape=shape,
                                                hdu_index=0, relative_to=".")

    assert len(array_container.output_shape) == 5
    assert array_container.output_shape == array_container.array.shape


def test_asdf_tree(header_filenames):
    tree = asdf_tree_from_filenames(header_filenames)
    assert isinstance(tree, dict)


def test_validator(header_filenames):
    headers = headers_from_filenames(header_filenames)
    headers[10]['NAXIS'] = 5
    with pytest.raises(ValueError) as excinfo:
        validate_headers(table_from_headers(headers))
        assert "NAXIS" in str(excinfo)


def test_dataset_from_fits(header_directory):
    dataset_from_fits(header_directory, "test_asdf.asdf")

    asdf_file = pathlib.Path(header_directory) / "test_asdf.asdf"
    assert asdf_file.exists()

    with asdf.open(asdf_file) as adf:
        assert isinstance(adf['dataset'], Dataset)

    asdf_file.unlink()
