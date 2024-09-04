import os
from unittest.mock import call

import pytest


@pytest.fixture
def tmp_sample_dir(tmp_path):
    old_path = os.environ.get("DKIST_SAMPLE_DIR", "")
    os.environ["DKIST_SAMPLE_DIR"] = str(tmp_path)
    yield tmp_path
    os.environ["DKIST_SAMPLE_DIR"] = old_path


def test_module_dir():
    import dkist.data.sample

    assert "VBI_AJQWW" in dir(dkist.data.sample)
    assert "VISP_BKPLX" in dir(dkist.data.sample)


@pytest.mark.parametrize("attrname", ["VBI_AJQWW", "VISP_BKPLX"])
def test_module_getattr(mocker, attrname):
    mock = mocker.patch("dkist.data.sample._get_sample_datasets")
    import dkist.data.sample

    getattr(dkist.data.sample, attrname)

    mock.assert_has_calls([call(attrname), call().__getitem__(0)])


@pytest.mark.internet_off
def test_fail(tmp_sample_dir):
    """
    No remote data means this test should fail.
    """
    with pytest.raises(RuntimeError, match="1 sample data files failed"):
        from dkist.data.sample import VISP_BKPLX  # noqa: F401
