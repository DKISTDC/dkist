import matplotlib
import pytest

matplotlib.use("Agg")


def pytest_configure(config):
    # pre-cache the IERS file for astropy to prevent downloads
    # which will cause errors with remote_data off
    from astropy.utils.iers import IERS_Auto; IERS_Auto.open()

    os.environ['DKIST_SKIP_UPDATE_SEARCH_VALUES'] = 'True'
    os.environ['IS_TEST_ENV'] = 'True'
