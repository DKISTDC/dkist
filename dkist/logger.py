"""
This module contains helpers to use the Python logger to show messages to users.

It is heavily insipired by Astropy's logger, but implemented independently
because Astropy warn you against directly using theirs.

This module sets up the following things:

* A `logging.Logger` subclass which:
  - Tracks the module which triggered the log call.
  - Overrides warnings.showwarnings so that subclasses of given warning classes are displayed using the logger.
* Sets up a ``log`` instance which uses the Astropy StreamHandler class to log to stdout and colourise the output.
"""
import os
import sys
import logging
import warnings

from astropy.logger import StreamHandler as AstropyStreamHandler
from astropy.utils.introspection import find_current_module

from dkist.utils.exceptions import DKISTWarning


class DKISTLogger(logging.Logger):
    """
    A knock off AstropyLogger.
    """
    _showwarning_orig = None

    def __init__(self, name, level=logging.NOTSET, *, capture_warning_classes=None):
        super().__init__(name, level=level)
        self.capture_warning_classes = tuple(capture_warning_classes) if capture_warning_classes is not None else ()

        self.enable_warnings_capture()

    def enable_warnings_capture(self):
        if self._showwarning_orig is None:
            self._showwarning_orig = warnings.showwarning
            warnings.showwarning = self._showwarning

    def disable_warnings_capture(self):
        if self._showwarning_orig is not None:
            warnings.showwarning = self._showwarning_orig
            self._showwarning_orig = None

    def makeRecord(
        self,
        name,
        level,
        pathname,
        lineno,
        msg,
        args,
        exc_info,
        func=None,
        extra=None,
        sinfo=None,
    ):
        if extra is None:
            extra = {}

        if "origin" not in extra:
            current_module = find_current_module(1, finddiff=[True, "logging"])
            if current_module is not None:
                extra["origin"] = current_module.__name__
            else:
                extra["origin"] = "unknown"

        return super().makeRecord(
            name,
            level,
            pathname,
            lineno,
            msg,
            args,
            exc_info,
            func=func,
            extra=extra,
            sinfo=sinfo,
        )

    def _showwarning(self, *args, **kwargs):
        # Bail out if we are not catching a warning from one of the given
        # classes (or subclasses)
        if not isinstance(args[0], self.capture_warning_classes):
            return self._showwarning_orig(*args, **kwargs)

        warning = args[0]
        message = f"{warning.__class__.__name__}: {args[0]}"

        mod_path = args[2]
        # Now that we have the module's path, we look through sys.modules to
        # find the module object and thus the fully-package-specified module
        # name.  The module.__file__ is the original source file name.
        mod_name = None
        mod_path, ext = os.path.splitext(mod_path)
        for name, mod in list(sys.modules.items()):
            try:
                # Believe it or not this can fail in some cases:
                # https://github.com/astropy/astropy/issues/2671
                path = os.path.splitext(getattr(mod, "__file__", ""))[0]
            except Exception:
                continue
            if path == mod_path:
                mod_name = mod.__name__
                break

        if mod_name is not None:
            self.warning(message, extra={"origin": mod_name})
        else:
            self.warning(message)


def setup_default_dkist_logger(name):
    log = DKISTLogger(name, level=logging.INFO, capture_warning_classes=[DKISTWarning])
    log.addHandler(AstropyStreamHandler())
    return log
