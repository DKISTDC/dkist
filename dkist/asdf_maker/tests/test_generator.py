import pathlib

import pytest

import gwcs
import gwcs.coordinate_frames as cf
from astropy.modeling import Model, models

from dkist.asdf_maker.generator import (asdf_tree_from_filenames, dataset_from_fits,
                                        gwcs_from_headers, headers_from_filenames,
                                        table_from_headers, validate_headers)
from dkist.dataset import Dataset


@pytest.fixture
def wcs(header_filenames):
    wcs = gwcs_from_headers(headers_from_filenames(header_filenames))
    assert isinstance(wcs, gwcs.WCS)
    return wcs


def test_reset(transform_builder):
    transform_builder._i = 2
    transform_builder.reset()
    assert transform_builder._i == 0


def test_transform(transform_builder):
    assert isinstance(transform_builder.transform, Model)


def test_frames(transform_builder):
    frames = transform_builder.frames
    assert all([isinstance(frame, cf.CoordinateFrame) for frame in frames])


def test_input_name_ordering(wcs):
    # Check the ordering of the input and output frames
    allowed_pixel_names = (('spatial x', 'spatial y', 'wavelength position', 'scan number',
                            'stokes'), ('wavelength', 'slit position', 'raster position',
                                        'scan number', 'stokes'))
    assert wcs.input_frame.axes_names in allowed_pixel_names


def test_output_name_ordering(wcs):
    allowed_world_names = (('latitude', 'longitude', 'wavelength', 'time', 'stokes'),
                           ('wavelength', 'latitude', 'longitude', 'time', 'stokes'))
    assert wcs.output_frame.axes_names in allowed_world_names


def test_output_frames(wcs):
    allowed_frame_orders = ((cf.CelestialFrame, cf.SpectralFrame, cf.TemporalFrame, cf.StokesFrame),
                            (cf.SpectralFrame, cf.CelestialFrame, cf.TemporalFrame, cf.StokesFrame))
    types = tuple((type(frame) for frame in wcs.output_frame.frames))
    assert types in allowed_frame_orders


def test_transform_models(wcs):
    # Test that there is one lookup table and two linear models for both the
    # wcses
    sms = wcs.forward_transform._leaflist
    smtypes = [type(m) for m in sms]
    assert sum(mt is models.Linear1D for mt in smtypes) == 2
    assert sum(mt is models.Tabular1D for mt in smtypes) == 1


def test_array_container_shape(header_filenames):
    from dkist.asdf_maker.generator import _preprocess_headers, references_from_filenames
    from dkist.io import DaskFITSArrayContainer, AstropyFITSLoader

    headers = headers_from_filenames(header_filenames, hdu=0)
    table_headers, sorted_filenames, sorted_headers = _preprocess_headers(headers, header_filenames)
    # Get the array shape
    shape = tuple((headers[0][f'DNAXIS{n}'] for n in range(headers[0]['DNAXIS'],
                                                           headers[0]['DAAXES'], -1)))
    # References from filenames
    array_container = references_from_filenames(sorted_filenames, sorted_headers, array_shape=shape,
                                                hdu_index=0, relative_to=".")

    assert len(array_container.output_shape) == 5
    assert array_container.output_shape == array_container.array.shape


def test_asdf_tree(header_filenames):
    tree = asdf_tree_from_filenames(header_filenames, "test_file.asdf")
    assert isinstance(tree, dict)


def test_validator(header_filenames):
    headers = headers_from_filenames(header_filenames)
    headers[10]['NAXIS'] = 5
    with pytest.raises(ValueError) as excinfo:
        validate_headers(table_from_headers(headers))
        assert "NAXIS" in str(excinfo)


def test_make_asdf(header_filenames, tmpdir):
    path = pathlib.Path(header_filenames[0])
    dataset_from_fits(path.parent, "test.asdf")
    assert (path.parent / "test.asdf").exists()
    assert isinstance(Dataset.from_directory(str(path.parent)), Dataset)
