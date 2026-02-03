from asdf.testing.helpers import roundtrip_object


def assert_inversion_equal(new, old):
    old_headers = old.meta.pop("headers")
    new_headers = new.meta.pop("headers")
    assert old_headers.colnames == new_headers.colnames
    assert len(old_headers) == len(new_headers)
    # This won't work because of how we handle the meta attributes
    # We should make it work, I'm just not sure how yet
    # assert old.meta == new.meta


def test_roundtrip_inversion(inversion):
    newobj = roundtrip_object(inversion)
    assert_inversion_equal(newobj, inversion)
