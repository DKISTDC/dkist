import os
import platform
from unittest.mock import call

import pytest

from dkist.utils.exceptions import DKISTDeprecationWarning


@pytest.fixture
def tmp_sample_dir(tmp_path):
    old_path = os.environ.get("DKIST_SAMPLE_DIR", "")
    os.environ["DKIST_SAMPLE_DIR"] = str(tmp_path)
    yield tmp_path
    os.environ["DKIST_SAMPLE_DIR"] = old_path


def test_module_dir():
    import dkist.data.sample  # noqa: PLC0415

    assert "VBI_L1_NZJTB" in dir(dkist.data.sample)
    assert "VISP_L1_KMUPT" in dir(dkist.data.sample)


@pytest.mark.parametrize("attrname", ["VBI_L1_NZJTB", "VISP_L1_KMUPT"])
def test_module_getattr(mocker, attrname):
    mock = mocker.patch("dkist.data.sample._get_sample_datasets")
    import dkist.data.sample  # noqa: PLC0415

    getattr(dkist.data.sample, attrname)

    mock.assert_has_calls([call(attrname), call().__getitem__(0)])


@pytest.mark.parametrize("attrname", ["VBI_AJQWW", "VISP_BKPLX"])
def test_module_getattr_deprecated(mocker, attrname):
    mock = mocker.patch("dkist.data.sample._get_sample_datasets")
    import dkist.data.sample  # noqa: PLC0415
    from dkist.data._sample import _DEPRECATED_NAMES  # noqa: PLC0415

    with pytest.warns(DKISTDeprecationWarning, match=attrname):
        getattr(dkist.data.sample, attrname)

    mock.assert_has_calls([call(_DEPRECATED_NAMES[attrname]), call().__getitem__(0)])


@pytest.mark.skipif(platform.system() == "Windows", reason="Internet not properly disabled on Windows")
@pytest.mark.internet_off
def test_fail(tmp_sample_dir):
    """
    No remote data means this test should fail.
    """
    with pytest.raises(RuntimeError, match="1 sample data files failed"):
        from dkist.data.sample import VISP_L1_KMUPT  # noqa: F401 PLC0415
