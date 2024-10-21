import warnings

import matplotlib as mpl
import pytest

mpl.use("Agg")


def pytest_configure(config):
    # pre-cache the IERS file for astropy to prevent downloads
    # which will cause errors with remote_data off
    from astropy.utils.iers import IERS_Auto
    IERS_Auto.open()


def pytest_addoption(parser):
    parser.addoption("--ds", action="store", help="Dataset provided as a string which can be parsed by load_dataset. This will override fixtures used in tests decorated with @accept_ds_from_cli.")
    parser.addoption("--tiled-ds", action="store", help="Tiled datasets provided as a string which can be parsed by load_dataset. These datasets will override fixtures used in tests decorated with @accept_tiled_ds_from_cli.")


def pytest_report_header(config, start_path):
    ds_str = config.getoption("--ds") or "None"
    tds_str = config.getoption("--tiled-ds") or "None"

    return [f"CLI dataset provided: {ds_str}",
            f"CLI tiled dataset provided: {tds_str}"]


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    report = yield
    if report.when == "call":
        try:
            ds = item.config.getoption("--ds")
            tds = item.config.getoption("--tiled-ds")
        except ValueError:
            # If CLI arguments can't be found, need to return gracefully
            warnings.warn("--ds and --tiled-ds were not found. Any supplied datasets were not used.")
            return report
        if ds and item.get_closest_marker("accept_cli_dataset"):
            report.nodeid += f"[{ds}]"
        if tds and item.get_closest_marker("accept_cli_tiled_dataset"):
            report.nodeid += f"[{tds}]"

    return report
