"""
Functionality for loading many DKIST FITS files into a single Dask array.
"""
from . import utils
from .file_manager import DKISTFileManager

__all__ = ["DKISTFileManager"]
