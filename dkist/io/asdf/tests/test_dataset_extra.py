import pytest

import asdf
from asdf.testing.helpers import roundtrip_object
from astropy.table import Table

from dkist.dataset import DatasetExtra


def assert_dataset_extra_equal(new, old):
    assert new.name == old.name
    assert new._header_rows == old._header_rows
    assert new.headers.colnames == old.headers.colnames
    assert len(new.headers) == len(old.headers)
    for col in new.headers.colnames:
        assert list(new.headers[col]) == list(old.headers[col])
    assert len(new._ears) == len(old._ears)
    for new_ear, old_ear in zip(new._ears, old._ears):
        assert new_ear.fileuri == old_ear.fileuri
        assert new_ear.shape == old_ear.shape
        assert new_ear.dtype == old_ear.dtype
        assert new_ear.target == old_ear.target


def test_roundtrip_dataset_extra(dataset_extra_obj):
    newobj = roundtrip_object(dataset_extra_obj)
    assert_dataset_extra_equal(newobj, dataset_extra_obj)


@pytest.fixture
def dataset_extras():
    headers = Table({"col1": [1, 2, 3, 4], "col2": ["a", "b", "c", "d"]})
    ears1 = [asdf.ExternalArrayReference("file1.fits", 0, "float64", (10, 10))]
    ears2 = [asdf.ExternalArrayReference("file2.fits", 1, "float64", (10, 10))]
    extra1 = DatasetExtra(
        name="extra1",
        full_header_table=headers,
        header_rows=[0, 1],
        ears=ears1,
    )
    extra2 = DatasetExtra(
        name="extra2",
        full_header_table=headers,
        header_rows=[2, 3],
        ears=ears2,
    )
    return extra1, extra2


def test_roundtrip_dataset_extra_with_header_rows(dataset_extras):
    newobj = roundtrip_object(dataset_extras[0])
    assert_dataset_extra_equal(newobj, dataset_extras[0])


def test_roundtrip_shared_header_table(tmp_path, dataset_extras):
    """
    Verify that two extras sharing the same full_header_table round-trip
    with their tables as the same object.
    """
    tree = {"extra1": dataset_extras[0], "extra2": dataset_extras[1]}
    fn = tmp_path / "extras.asdf"
    with asdf.AsdfFile(tree) as af:
        af.write_to(fn)

    # Ensure the table only gets written once
    with open(fn, mode="rb") as raw_asdf:
        bytes = raw_asdf.read()
        end_yml = bytes.find(b"...")
        contents = bytes[:end_yml].decode("utf-8")
        assert contents.count("tag:astropy.org:astropy/table/table") == 1

    with asdf.open(fn) as af:
        loaded1 = af.tree["extra1"]
        loaded2 = af.tree["extra2"]
        assert loaded1._full_header_table is loaded2._full_header_table
        assert len(loaded1.headers) == 2
        assert len(loaded2.headers) == 2
