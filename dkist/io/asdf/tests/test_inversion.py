from asdf.testing.helpers import roundtrip_object


def assert_inversion_equal(new, old):
    old_headers = old.meta.pop("headers")
    new_headers = new.meta.pop("headers")
    assert old_headers.colnames == new_headers.colnames
    assert len(old_headers) == len(new_headers)
    assert old.meta == new.meta
    old.meta["headers"] = old_headers
    new.meta["headers"] = new_headers
    assert old.wcs.name == new.wcs.name
    assert len(old.wcs.available_frames) == len(new.wcs.available_frames)
    ac_new = new.files.fileuri_array
    ac_old = old.files.fileuri_array
    assert (ac_new == ac_old).all()
    assert old.unit == new.unit
    assert old.mask == new.mask


def test_roundtrip_inversion(inversion):
    newobj = roundtrip_object(inversion)
    assert_inversion_equal(newobj, inversion)
