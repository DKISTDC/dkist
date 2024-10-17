import matplotlib as mpl

mpl.use("Agg")


def pytest_configure(config):
    # pre-cache the IERS file for astropy to prevent downloads
    # which will cause errors with remote_data off
    from astropy.utils.iers import IERS_Auto
    IERS_Auto.open()
