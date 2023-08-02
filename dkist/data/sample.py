import pathlib

from astropy.io import fits

__all__ = ["VISP_HEADER"]

_data_dir = pathlib.Path(__file__).parent

VISP_HEADER = fits.Header.fromtextfile(_data_dir / "VISP_HEADER.hdr")
