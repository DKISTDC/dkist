from pathlib import Path
from importlib import resources

import pytest

import asdf
from asdf.tests import helpers

from dkist.io import FileManager
from dkist.io.loaders import AstropyFITSLoader


@pytest.fixture
def tagobj(request):
    """
    A fixture to lookup other fixtures.
    """
    return request.getfixturevalue(request.param)


@pytest.fixture
def array_container():
    return FileManager(['test1.fits', 'test2.fits'], 0, 'float', (10, 10),
                       loader=AstropyFITSLoader)


@pytest.mark.parametrize("tagobj",
                         ["array_container",
                          "dataset"],
                         indirect=True)
def test_tags(tagobj, tmpdir):
    tree = {'object': tagobj}
    helpers.assert_roundtrip_tree(tree, tmpdir)


def test_save_dataset_without_file_schema(tmpdir, dataset):
    tree = {'dataset': dataset}
    with asdf.AsdfFile(tree) as afile:
        afile.write_to(Path(tmpdir / "test.asdf"))


def test_save_dataset_with_file_schema(tmpdir, dataset):
    tree = {'dataset': dataset}
    with resources.path("dkist.io", "level_1_dataset_schema.yaml") as schema_path:
        with asdf.AsdfFile(tree, custom_schema=schema_path.as_posix()) as afile:
            afile.write_to(Path(tmpdir / "test.asdf"))
