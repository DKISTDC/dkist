"""
Search attrs for DKIST data.
"""

from sunpy.net.attr import SimpleAttr  # noqa
from sunpy.net.attrs import Instrument, Level, Time, Wavelength
from sunpy.net.vso.attrs import Physobs, Provider

__all__ = ['Provider', 'Physobs', 'Level', 'Wavelength', 'Instrument', 'Time']

# A list of attrs we are inheriting from SunPy
_imported_attrs = [Provider, Physobs, Level, Wavelength, Instrument, Time]

# Trick the docs into thinking these belong here.
for attr in _imported_attrs:
    attr.__module__ = __name__
