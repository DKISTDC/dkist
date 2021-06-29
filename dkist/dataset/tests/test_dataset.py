import os
from pathlib import Path

import dask.array as da
import pytest

import asdf
import astropy.units as u
import gwcs
from astropy.tests.helper import assert_quantity_allclose

from dkist.data.test import rootdir
from dkist.dataset import Dataset
from dkist.io.array_containers import BaseFITSArrayContainer
from dkist.utils.globus import DKIST_DATA_CENTRE_DATASET_PATH, DKIST_DATA_CENTRE_ENDPOINT_ID


@pytest.fixture
def invalid_asdf(tmpdir):
    filename = Path(tmpdir / "test.asdf")
    tree = {'spam': 'eggs'}
    with asdf.AsdfFile(tree=tree) as af:
        af.write_to(filename)
    return filename


def test_load_invalid_asdf(invalid_asdf):
    with pytest.raises(TypeError):
        Dataset.from_asdf(invalid_asdf)


def test_repr(dataset, dataset_3d):
    r = repr(dataset)
    assert str(dataset.data) in r
    r = repr(dataset_3d)
    assert str(dataset_3d.data) in r


def test_wcs_roundtrip(dataset):
    p = (10*u.pixel, 10*u.pixel)
    w = dataset.wcs.pixel_to_world(*p)
    p2 = dataset.wcs.world_to_pixel(w)
    assert_quantity_allclose(p, p2 * u.pix)


def test_wcs_roundtrip_3d(dataset_3d):
    p = (10*u.pixel, 10*u.pixel, 10*u.pixel)
    w = dataset_3d.wcs.pixel_to_world(*p)
    p2 = dataset_3d.wcs.world_to_pixel(*w) * u.pix
    assert_quantity_allclose(p[:2], p2[:2])
    assert_quantity_allclose(p[2], p2[2])


def test_dimensions(dataset, dataset_3d):
    for ds in [dataset, dataset_3d]:
        assert_quantity_allclose(ds.dimensions, ds.data.shape*u.pix)


def test_load_from_directory():
    ds = Dataset.from_directory(os.path.join(rootdir, 'EIT'))
    assert isinstance(ds.data, da.Array)
    assert isinstance(ds.wcs, gwcs.WCS)
    assert_quantity_allclose(ds.dimensions, (11, 128, 128)*u.pix)


def test_from_directory_no_asdf(tmpdir):
    with pytest.raises(ValueError) as e:
        Dataset.from_directory(tmpdir)
        assert "No asdf file found" in str(e)


def test_from_not_directory():
    with pytest.raises(ValueError) as e:
        Dataset.from_directory(rootdir/"notadirectory")
        assert "directory argument" in str(e)


def test_from_directory_not_dir():
    with pytest.raises(ValueError) as e:
        Dataset.from_directory(rootdir / 'EIT' / 'eit_2004-03-01T00_00_10.515000.asdf')
        assert "must be a directory" in str(e)


def test_crop_few_slices(dataset_4d):
    sds = dataset_4d[0, 0]
    assert sds.wcs.world_n_dim == 2


def test_array_container():
    dataset = Dataset.from_directory(os.path.join(rootdir, 'EIT'))
    assert dataset.array_container is dataset._array_container
    with pytest.raises(AttributeError):
        dataset.array_container = 10

    assert len(dataset.array_container.filenames) == 11
    assert len(dataset.filenames) == 11

    assert isinstance(dataset[5]._array_container, BaseFITSArrayContainer)
    assert len(dataset[5].filenames) == 1


def test_no_filenames(dataset_3d):
    assert dataset_3d.filenames == []


def test_download(mocker, dataset):
    mocker.patch("dkist.dataset.dataset.watch_transfer_progress",
                 autospec=True)
    mocker.patch("dkist.dataset.dataset.get_local_endpoint_id",
                 autospec=True, return_value="mysecretendpoint")
    mocker.patch("dkist.dataset.dataset.get_transfer_client",
                 autospec=True)
    start_mock = mocker.patch("dkist.dataset.dataset.start_transfer_from_file_list",
                              autospec=True, return_value="1234")

    base_path = Path(DKIST_DATA_CENTRE_DATASET_PATH.format(**dataset.meta))
    file_list = dataset.filenames + ["/{bucket}/{primaryProposalId}/{datasetId}/test_dataset.asdf".format(**dataset.meta)]
    file_list = [base_path / fn for fn in file_list]

    dataset.download()

    start_mock.assert_called_once_with(DKIST_DATA_CENTRE_ENDPOINT_ID,
                                       "mysecretendpoint",
                                       Path("/~/test_proposal/test_dataset"),
                                       file_list)


def test_download_no_progress(mocker, dataset):
    progress_mock = mocker.patch("dkist.dataset.dataset.watch_transfer_progress",
                                 autospec=True)
    mocker.patch("dkist.dataset.dataset.get_local_endpoint_id",
                 autospec=True, return_value="mysecretendpoint")
    tc_mock = mocker.patch("dkist.dataset.dataset.get_transfer_client",
                           autospec=True)
    start_mock = mocker.patch("dkist.dataset.dataset.start_transfer_from_file_list",
                              autospec=True, return_value="1234")

    base_path = Path(DKIST_DATA_CENTRE_DATASET_PATH.format(**dataset.meta))
    file_list = dataset.filenames + ["/{bucket}/{primaryProposalId}/{datasetId}/test_dataset.asdf".format(**dataset.meta)]
    file_list = [base_path / fn for fn in file_list]

    dataset.download(progress=False)

    start_mock.assert_called_once_with(DKIST_DATA_CENTRE_ENDPOINT_ID,
                                       "mysecretendpoint",
                                       Path("/~/test_proposal/test_dataset"),
                                       file_list)

    progress_mock.assert_not_called()
    tc_mock.return_value.task_wait.assert_called_once_with("1234", timeout=1e6)
