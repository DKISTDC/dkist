import logging
import warnings

import pytest

from dkist import log
from dkist.utils.exceptions import DKISTUserWarning, DKISTWarning


def test_debug_log(caplog_dkist):
    # By default the level is set to INFO so we shouldn't get anything here.
    log.debug("test_debug_log")
    assert caplog_dkist.record_tuples == []


def test_info_log(caplog_dkist, capsys):
    log.info("test_info_log")
    assert caplog_dkist.record_tuples == [("dkist", logging.INFO, "test_info_log")]

    captured = capsys.readouterr()
    assert "INFO: test_info_log [dkist.tests.test_logger]" in captured.out


def test_warning_log(caplog_dkist, capsys):
    log.warning("test_warning_log")

    assert caplog_dkist.record_tuples == [("dkist", logging.WARNING, "test_warning_log")]
    captured = capsys.readouterr()
    assert "WARNING: test_warning_log [dkist.tests.test_logger]" in captured.err


def test_error_log(caplog_dkist, capsys):
    log.error("test_error_log")

    assert caplog_dkist.record_tuples == [("dkist", logging.ERROR, "test_error_log")]
    captured = capsys.readouterr()
    assert "ERROR: test_error_log [dkist.tests.test_logger]" in captured.err


def test_warning_capture(caplog_dkist, capsys):
    log.disable_warnings_capture()
    log.enable_warnings_capture()

    with warnings.catch_warnings():
        warnings.simplefilter("always")
        warnings.warn("Test warning", DKISTWarning)
        assert caplog_dkist.record_tuples == [("dkist", logging.WARNING, "DKISTWarning: Test warning")]

    captured = capsys.readouterr()
    assert "WARNING: DKISTWarning: Test warning [dkist.tests.test_logger]" in captured.err


def test_subclass_warning_capture(caplog_dkist, capsys):
    log.disable_warnings_capture()
    log.enable_warnings_capture()

    with warnings.catch_warnings():
        warnings.simplefilter("always")
        warnings.warn("Test warning", DKISTUserWarning)
        assert caplog_dkist.record_tuples == [("dkist", logging.WARNING, "DKISTUserWarning: Test warning")]

    captured = capsys.readouterr()
    assert "WARNING: DKISTUserWarning: Test warning [dkist.tests.test_logger]" in captured.err


def test_no_warning_capture(caplog_dkist, capsys):
    log.disable_warnings_capture()

    with pytest.warns(match="Test warning"):
        with warnings.catch_warnings():
            # To ensure that disable works, we enable it and then disable it
            # again after pytest is done with all it's stuff
            log.enable_warnings_capture()
            log.disable_warnings_capture()
            warnings.simplefilter("always")
            warnings.warn("Test warning", DKISTWarning)
            assert caplog_dkist.record_tuples == []

    captured = capsys.readouterr()
    assert captured.err == ""


def test_not_class_warning_capture(caplog_dkist, capsys):
    log.disable_warnings_capture()

    with pytest.warns(match="Test warning"):
        with warnings.catch_warnings():
            # We must re-enable capture in the context manager
            log.enable_warnings_capture()
            warnings.simplefilter("always")
            warnings.warn("Test warning", Warning)
            assert caplog_dkist.record_tuples == []

    captured = capsys.readouterr()
    assert captured.err == ""
