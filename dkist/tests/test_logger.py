import logging

from dkist import log


def test_debug_log(caplog_dkist):
    # By default the level is set to INFO so we shouldn't get anything here.
    log.debug("test_debug_log")
    assert caplog_dkist.record_tuples == []


def test_debug_on(caplog_dkist, capsys):
    log.setLevel("DEBUG")

    log.debug("test_debug_log")
    assert caplog_dkist.record_tuples == [("dkist", logging.DEBUG, "test_debug_log")]

    captured = capsys.readouterr()
    assert "DEBUG: test_debug_log [dkist.tests.test_logger]" in captured.out


def test_info_log(caplog_dkist, capsys):
    log.info("test_info_log")
    assert caplog_dkist.record_tuples == [("dkist", logging.INFO, "test_info_log")]

    captured = capsys.readouterr()
    assert "WARNING: test_warning_log [dkist.tests.test_logger]" in captured.out


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
