from pathlib import Path

import numpy as np
import pytest

from asdf.testing.helpers import roundtrip_object

from dkist import load_dataset


def assert_inversion_equal(new, old):
    old_headers = old.meta["headers"]
    new_headers = new.meta["headers"]
    assert old_headers.colnames == new_headers.colnames
    assert len(old_headers) == len(new_headers)
    # This won't work because of how we handle the meta attributes
    # We should make it work, I'm just not sure how yet
    # assert old.meta == new.meta


def test_roundtrip_inversion(inversion):
    newobj = roundtrip_object(inversion)
    assert_inversion_equal(newobj, inversion)


@pytest.mark.parametrize("slice", [np.s_[0], np.s_[0, 0]])
def test_save_inversion_sliced(inversion, slice):
    fname = "inv-save-test.asdf"
    ds = inversion

    ds1 = ds[slice]
    ds1.save(fname, overwrite=True)

    ds2 = load_dataset(fname)

    assert_inversion_equal(ds1, ds2)


def test_save_inversion_to_existing_file(inversion):
    fname = "inv-overwrite-test.asdf"
    ds = inversion

    ds.save(fname)
    with pytest.raises(FileExistsError):
        ds.save(fname)

    ds1 = ds[0]
    ds1.save(fname, overwrite=True)

    ds2 = load_dataset(fname)

    assert_inversion_equal(ds1, ds2)

    # Tidying. I'm sure there's a better fixture-based way to do this
    Path(fname).unlink()
