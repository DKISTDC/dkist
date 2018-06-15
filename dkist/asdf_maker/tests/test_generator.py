import pytest

import gwcs
import gwcs.coordinate_frames as cf
from astropy.modeling import Model

from dkist.asdf_maker.generator import (gwcs_from_headers,
                                        asdf_tree_from_filenames,
                                        headers_from_filenames, validate_headers)


def test_reset(transform_builder):
    transform_builder._i = 2
    transform_builder.reset()
    assert transform_builder._i == 0


def test_transform(transform_builder):
    assert isinstance(transform_builder.transform, Model)


def test_frames(transform_builder):
    frames = transform_builder.frames
    assert all([isinstance(frame, cf.CoordinateFrame) for frame in frames])


def test_gwcs_from_files(header_filenames):
    w = gwcs_from_headers(headers_from_filenames(header_filenames))
    assert isinstance(w, gwcs.WCS)


def test_asdf_tree(header_filenames):
    tree = asdf_tree_from_filenames(header_filenames)
    assert isinstance(tree, dict)


def test_validator(header_filenames):
    headers = headers_from_filenames(header_filenames)
    headers[10]['NAXIS'] = 5
    with pytest.raises(ValueError) as excinfo:
        validate_headers(headers)
        assert "NAXIS" in str(excinfo)
