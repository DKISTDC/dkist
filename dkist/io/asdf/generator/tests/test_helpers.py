import os
from pathlib import Path

import numpy as np
import pytest

import asdf
import astropy.units as u
from astropy.io import fits
from astropy.modeling import Model, models
from astropy.time import Time

from dkist.io.asdf.generator.generator import asdf_tree_from_filenames, references_from_filenames
from dkist.io.asdf.generator.helpers import headers_from_filenames


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
