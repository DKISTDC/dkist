"""
Functionality for loading many DKIST FITS files into a single Dask array.
"""
from .file_manager import DKISTFileManager
from .utils import filemanager_info_str

__all__ = ["DKISTFileManager"]
