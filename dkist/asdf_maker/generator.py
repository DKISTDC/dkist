import astropy.units as u
from astropy.io import fits
from astropy.table import Table
from astropy.time import Time
from sunpy.coordinates import Helioprojective

import gwcs.coordinate_frames as cf
from gwcs.lookup_table import LookupTable

from dkist.asdf_maker.helpers import (references_from_filenames, make_asdf,
                                      spatial_model_from_quantity, linear_spectral_model,
                                      linear_time_model, time_model_from_date_obs,
                                      spatial_model_from_header)


def headers_from_filenames(filenames, hdu=0):
    """
    A generator to get the headers from filenames.
    """
    return (fits.getheader(fname, hdu=hdu) for fname in filenames)


def validate_headers(headers):
    """
    Given a bunch of headers, validate that they form a coherent set. This
    function also adds the headers to a list as they are read from the file.

    Parameters
    ----------

    headers :  iterator
        An iterator of headers.

    Returns
    -------
    out_headers : `list`
        A list of headers.
    """
    out_headers = []
    h0 = next(headers)
    out_headers.append(h0)

    t = Table(names=h0.keys())
    t.add_row(h0)

    for h in headers:
        t.add_row(h)
        out_headers.append(h)

    """
    Let's do roughly the minimal amount of verification here.
    """

    # For some keys all the values must be the same
    same_keys = ['NAXIS', 'DNAXIS']
    naxis_same_keys = ['NAXISn', 'CTYPEn', 'CRPIXn', 'CRVALn']
    dnaxis_same_keys = ['DNAXISn', 'DTYPEn', 'DPNAMEn', 'DWNAMEn']
    # Expand n in NAXIS keys
    for nsk in naxis_same_keys:
        for naxis in range(1, t['NAXIS'][0] + 1):
            same_keys.append(nsk.replace('n', naxis))
    # Expand n in DNAXIS keys
    for dsk in dnaxis_same_keys:
        for dnaxis in range(1, t['DNAXIS'][0] + 1):
            same_keys.append(nsk.replace('n', dnaxis))

    validate_t = t[same_keys]
    assert (validate_t == validate_t[0]).all()

    return out_headers


def build_pixel_frame(header):
    """
    Given a header, build the input
    `gwcs.coordinate_frames.CoordinateFrame` object describing the pixel frame.

    Parameters
    ----------

    header : `dict`
        A fits header.

    Returns
    -------

    pixel_frame : `gwcs.coordinate_frames.CoordinateFrame`
        The pixel frame.
    """
    axes_types = [header[f'DTYPE{n}'] for n in range(header['DNAXIS'], 0, -1)]

    return cf.CoordinateFrame(naxes=header['DNAXIS'],
                              axes_type=axes_types,
                              axes_order=range(header['DNAXIS']),
                              unit=[u.pixel]*header['DNAXIS'],
                              axes_names=[header[f'DPNAME{n}'] for n in range(header['DNAXIS'], 0, -1)],
                              name='pixel')


class TransformBuilder:
    """
    This class builds compound models and frames in order when given axes types.
    """

    def __init__(self, headers):
        self.headers = headers
        self.header = self.headers[0]
        self.reset()
        self._build()

    @property
    def frames(self):
        """
        The coordinate frames, in Python order.
        """
        return self._frames

    @property
    def transform(self):
        """
        Return the compound model.
        """
        tf = self._transforms[0]

        for i in range(1, len(tf)):
            tf = tf & self._transforms[i]

        return tf

    """
    Internal Stuff
    """

    def _build(self):
        """
        Build the state of the thing.
        """
        type_map = {'STOKES': self.make_stokes,
                    'TEMPORAL': self.make_temporal,
                    'SPECTRAL': self.make_spectral,
                    'SPATIAL': self.make_spatial}

        while self._i < self.header['DNAXIS']:  # < because FITS is i+1
            atype = self.axes_types[self._i]
            type_map[atype]()

    @property
    def axes_types(self):
        """
        The list of DTYPEn for the first header.
        """
        return [self.header[f'DTYPE{n}'] for n in range(self.header['DNAXIS'], 0, -1)]

    def reset(self):
        """
        Reset the builder.
        """
        self._i = 0
        self._frames = []
        self._transforms = []

    def n(self, i):
        """
        Convert a Python index ``i`` to a FITS order index for keywords ``n``.
        """
        return range(self.header['DNAXIS'], 0, -1)[i]

    def get_units(self, *iargs):
        """
        Get zee units
        """
        u = [self.header.get(f'DUNIT{self.n(i)}', None) for i in iargs]

        return u

    def make_stokes(self):
        """
        Add a stokes axes to the builder.
        """
        n = self.n(self._i)

        name = self.header[f'DWNAME{n}']
        self._frames.append(cf.StokesFrame(axes_order=(self._i,), name=name))
        self._transforms.append(LookupTable([0, 1, 2, 3] * u.pixel))

        self._i += 1

    def make_temporal(self):
        """
        Add a temporal axes to the builder.
        """
        n = self.n(self._i)
        name = self.header[f'DWNAME{n}']
        self._frames.append(cf.TemporalFrame(axes_order=(self._i,),
                                             name=name,
                                             unit=self.get_units(self._i),
                                             reference_time=Time(self.header['DATE-BGN'])))
        self._transforms.append(time_model_from_date_obs([e['DATE-OBS'] for e in self.headers],
                                                         self.header['DATE-BGN']))

        self._i += 1

    def make_spatial(self):
        """
        Add a helioprojective spatial pair to the builder.

        .. note::
            This increments the counter by two.

        """
        i = self._i
        n = self.n(self._i)
        name = self.header[f'DWNAME{n}']
        name = name.split(' ')[0]
        axes_names = [(self.header[f'DWNAME{n}'].rsplit(' ')[1]) for n in (i, self.n(i+1))]

        obstime = Time(self.header['DATE-BGN'])
        self._frames.append(cf.CelestialFrame(axes_order=(i, i+1), name=name,
                                              reference_frame=Helioprojective(obstime=obstime),
                                              axes_names=axes_names,
                                              unit=self.get_units(self._i, self._i+1)))

        self._transforms.append(spatial_model_from_header(self.header))

        self._i += 2

    def make_spectral(self):
        """
        Add a spectral axes.
        """
        n = self.n(self._i)
        name = self.header[f'DWNAME{n}']
        self._frames.append(cf.SpectralFrame(axes_order=(self._i,),
                                             unit=self.get_units(self._i),
                                             name=name))
        self._transforms.append(linear_spectral_model(self.header[f'CDELT{n}']*u.nm,
                                                      self.header[f'CRVAL{n}']*u.nm))

        self._i += 1


def gwcs_from_filenames(filenames, hdu=0):
    """
    Given an iterable of filenames, build a gwcs for the dataset.
    """

    # headers is an iterator
    headers = headers_from_filenames(filenames, hdu=hdu)

    # headers is a now list
    headers = validate_headers(headers)

    # Now we know the headers are consistent, a lot of parts only need the first one.
    header = headers[0]

    pixel_frame = build_pixel_frame(header)

    # The physical types of the axes
    # axes_types = [header[f'DTYPE{n}'] for n in range(header['DNAXIS'], 0, -1)]
