import matplotlib as mpl

mpl.use("Agg")


def pytest_configure(config):
    # pre-cache the IERS file for astropy to prevent downloads
    # which will cause errors with remote_data off
    from astropy.utils.iers import IERS_Auto
    IERS_Auto.open()


def pytest_addoption(parser):
    parser.addoption("--ds", action="store", help="Comma-separated list of datasets provided as strings which can be parsed by load_dataset. These datasets will override fixtures used in tests decorated with @accept_ds_from_cli.")
