from asdf.testing.helpers import roundtrip_object


def assert_dataset_extra_equal(new, old):
    assert new.name == old.name
    assert new.headers.colnames == old.headers.colnames
    assert len(new.headers) == len(old.headers)
    assert len(new._ears) == len(old._ears)
    for new_ear, old_ear in zip(new._ears, old._ears):
        assert new_ear.fileuri == old_ear.fileuri
        assert new_ear.shape == old_ear.shape
        assert new_ear.dtype == old_ear.dtype
        assert new_ear.target == old_ear.target


def test_roundtrip_dataset_extra(dataset_extra_obj):
    newobj = roundtrip_object(dataset_extra_obj)
    assert_dataset_extra_equal(newobj, dataset_extra_obj)
