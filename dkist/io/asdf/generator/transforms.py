"""
Functionality relating to creating gWCS frames and Astropy models from SPEC 214 headers.
"""
import numpy as np

import astropy.units as u
import gwcs
import gwcs.coordinate_frames as cf
from astropy.modeling.models import (AffineTransformation2D, Linear1D, Multiply,
                                     Pix2Sky_TAN, RotateNative2Celestial, Shift, Tabular1D)
from astropy.time import Time
from sunpy.coordinates import Helioprojective

__all__ = ['TransformBuilder', 'spectral_model_from_framewave',
           'time_model_from_date_obs', 'generate_lookup_table',
           'linear_time_model', 'linear_spectral_model',
           'spatial_model_from_quantity', 'spatial_model_from_header']


def spatial_model_from_quantity(crpix1, crpix2, cdelt1, cdelt2, pc, crval1,
                                crval2, lon_pole, projection='TAN'):
    """
    Given quantity representations of a HPLx FITS WCS return a model for the
    spatial transform.

    The ordering of ctype1 and ctype2 should be LON, LAT
    """

    # TODO: Find this from somewhere else or extend it or something
    projections = {'TAN': Pix2Sky_TAN()}

    shiftu = Shift(-crpix1) & Shift(-crpix2)
    scale = Multiply(cdelt1) & Multiply(cdelt2)
    rotu = AffineTransformation2D(pc, translation=(0, 0)*u.arcsec)
    tanu = projections[projection]
    skyrotu = RotateNative2Celestial(crval1, crval2, lon_pole)
    return shiftu | scale | rotu | tanu | skyrotu


def spatial_model_from_header(header):
    """
    Given a FITS compliant header with CTYPEx,y as HPLN, HPLT return a
    `~astropy.modeling.CompositeModel` for the transform.

    This function finds the HPLN and HPLT keys in the header and returns a
    model in Lon, Lat order.
    """
    latind = None
    lonind = None
    for k, v in header.items():
        if isinstance(v, str) and "HPLN" in v:
            lonind = int(k[5:])
        if isinstance(v, str) and "HPLT" in v:
            latind = int(k[5:])

    if latind is None or lonind is None:
        raise ValueError("Could not extract HPLN and HPLT from the header.")

    latproj = header[f'CTYPE{latind}'][5:]
    lonproj = header[f'CTYPE{lonind}'][5:]

    if latproj != lonproj:
        raise ValueError("The projection of the two spatial axes did not match.")  # pragma: no cover

    cunit1, cunit2 = u.Unit(header[f'CUNIT{lonind}']), u.Unit(header[f'CUNIT{latind}'])
    crpix1, crpix2 = header[f'CRPIX{lonind}'] * u.pix, header[f'CRPIX{latind}'] * u.pix
    crval1, crval2 = (header[f'CRVAL{lonind}'] * cunit1, header[f'CRVAL{latind}'] * cunit2)
    cdelt1, cdelt2 = (header[f'CDELT{lonind}'] * (cunit1 / u.pix),
                      header[f'CDELT{latind}'] * (cunit2 / u.pix))
    pc = np.matrix([[header[f'PC{lonind}_{lonind}'], header[f'PC{lonind}_{latind}']],
                    [header[f'PC{latind}_{lonind}'], header[f'PC{latind}_{latind}']]]) * cunit1

    lonpole = header.get("LONPOLE")
    if not lonpole and latproj == "TAN":
        lonpole = 180

    if not lonpole:
        raise ValueError("LONPOLE not specified and not known for projection {latproj}")

    return spatial_model_from_quantity(crpix1, crpix2, cdelt1, cdelt2, pc,
                                       crval1, crval2, lonpole * u.deg,
                                       projection=latproj)


@u.quantity_input
def linear_spectral_model(spectral_width: u.nm, reference_val: u.nm):
    """
    Linear model in a spectral dimension. The reference pixel is always 0.
    """
    return Linear1D(slope=spectral_width / (1 * u.pix), intercept=reference_val)


@u.quantity_input
def linear_time_model(cadence: u.s, reference_val: u.s = 0*u.s):
    """
    Linear model in a temporal dimension. The reference pixel is always 0.
    """
    if not reference_val:
        reference_val = 0 * cadence.unit
    return Linear1D(slope=cadence / (1 * u.pix), intercept=reference_val)


def generate_lookup_table(lookup_table, interpolation='linear', points_unit=u.pix, **kwargs):
    if not isinstance(lookup_table, u.Quantity):
        raise TypeError("lookup_table must be a Quantity.")

    # The integer location is at the centre of the pixel.
    points = (np.arange(lookup_table.size) - 0) * points_unit

    kwargs = {
        'bounds_error': False,
        'fill_value': np.nan,
        'method': interpolation,
        **kwargs
        }

    return Tabular1D(points, lookup_table, **kwargs)


def time_model_from_date_obs(date_obs, date_bgn=None):
    """
    Return a time model that best fits a list of dateobs's.
    """
    if not date_bgn:
        date_bgn = date_obs[0]
    date_obs = Time(date_obs)
    date_bgn = Time(date_bgn)

    deltas = date_bgn - date_obs

    # Work out if we have a uniform delta (i.e. a linear model)
    ddelta = (deltas.to(u.s)[:-1] - deltas.to(u.s)[1:])

    # If the length of the axis is one, then return a very simple model
    if ddelta.size == 0:
        return linear_time_model(cadence=0*u.s, reference_val=0*u.s)
    elif u.allclose(ddelta[0], ddelta):
        slope = ddelta[0]
        intercept = 0 * u.s
        return linear_time_model(cadence=slope, reference_val=intercept)
    else:
        print(f"Creating tabular temporal axis. ddeltas: {ddelta}")
        return generate_lookup_table(deltas.to(u.s))


def spectral_model_from_framewave(framewav):
    """
    Construct a linear or lookup table model for wavelength based on the
    framewav keys.
    """
    framewav = u.Quantity(framewav, unit=u.nm)
    wave_bgn = framewav[0]

    deltas = wave_bgn - framewav
    ddeltas = (deltas[:-1] - deltas[1:])
    # If the length of the axis is one, then return a very simple model
    if ddeltas.size == 0:
        return linear_spectral_model(0*u.nm, wave_bgn)
    if u.allclose(ddeltas[0], ddeltas):
        slope = ddeltas[0]
        return linear_spectral_model(slope, wave_bgn)
    else:
        print(f"creating tabular wavelength axis. ddeltas: {ddeltas}")
        return generate_lookup_table(framewav)


class TransformBuilder:
    """
    This class builds compound models and frames in order when given axes types.
    """

    def __init__(self, headers):
        self.header = headers[0]

        # Reshape the headers to match the Dataset shape, so we can extract headers along various axes.
        shape = tuple(self.header[f'DNAXIS{n}'] for n in range(self.header['DNAXIS'],
                                                               self.header['DAAXES'], -1))
        arr_headers = np.empty(shape, dtype=object)
        for i in range(arr_headers.size):
            arr_headers.flat[i] = headers[i]

        self.pixel_shape = tuple(self.header[f'DNAXIS{n}'] for n in range(1, self.header['DNAXIS'] + 1))
        self.headers = arr_headers
        self.reset()
        self._build()

    @property
    def pixel_frame(self):
        """
        A `gwcs.coordinate_frames.CoordinateFrame` object describing the pixel frame.
        """
        return cf.CoordinateFrame(naxes=self.header['DNAXIS'],
                                  axes_type=self.axes_types,
                                  axes_order=range(self.header['DNAXIS']),
                                  unit=[u.pixel]*self.header['DNAXIS'],
                                  axes_names=[self.header[f'DPNAME{n}'] for n in range(1, self.header['DNAXIS'] + 1)],
                                  name='pixel')

    @property
    def gwcs(self):
        """
        `gwcs.WCS` object representing these headers.
        """
        world_frame = cf.CompositeFrame(self.frames)

        out_wcs = gwcs.WCS(forward_transform=self.transform,
                           input_frame=self.pixel_frame,
                           output_frame=world_frame)
        out_wcs.pixel_shape = self.pixel_shape
        out_wcs.array_shape = self.pixel_shape[::-1]

        return out_wcs

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

        for i in range(1, len(self._transforms)):
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

        xx = 0
        while self._i < self.header['DNAXIS']:  # < because FITS is i+1
            atype = self.axes_types[self._i]
            type_map[atype]()
            xx += 1
            if xx > 100:
                raise ValueError("Infinite loop in header parsing")  # pragma: no cover

    @property
    def axes_types(self):
        """
        The list of DTYPEn for the first header.
        """
        return [self.header[f'DTYPE{n}'] for n in range(1, self.header['DNAXIS'] + 1)]

    def reset(self):
        """
        Reset the builder.
        """
        self._i = 0
        self._frames = []
        self._transforms = []

    @property
    def n(self):
        """
        The FITS index of the current dimension.
        """
        return self._n(self._i)

    def _n(self, i):
        """
        Convert a Python index ``i`` to a FITS order index for keywords ``n``.
        """
        # return range(self.header['DNAXIS'], 0, -1)[i]
        return i + 1

    @property
    def slice_for_n(self):
        i = self._i - self.header['DAAXES']
        naxes = self.header['DEAXES']
        ss = [0] * naxes
        ss[i] = slice(None)
        return ss[::-1]

    @property
    def slice_headers(self):
        return self.headers[self.slice_for_n]

    def get_units(self, *iargs):
        """
        Get zee units
        """
        u = [self.header.get(f'DUNIT{self._n(i)}', None) for i in iargs]

        return u

    def make_stokes(self):
        """
        Add a stokes axes to the builder.
        """
        name = self.header[f'DWNAME{self.n}']
        self._frames.append(cf.StokesFrame(axes_order=(self._i,), name=name))
        self._transforms.append(generate_lookup_table([0, 1, 2, 3] * u.one, interpolation='nearest'))
        self._i += 1

    def make_temporal(self):
        """
        Add a temporal axes to the builder.
        """

        name = self.header[f'DWNAME{self.n}']
        self._frames.append(cf.TemporalFrame(axes_order=(self._i,),
                                             name=name,
                                             axes_names=(name,),
                                             unit=self.get_units(self._i),
                                             reference_frame=Time(self.header['DATE-BGN'])))
        self._transforms.append(time_model_from_date_obs([e['DATE-OBS'] for e in self.slice_headers],
                                                         self.header['DATE-BGN']))

        self._i += 1

    def make_spatial(self):
        """
        Add a helioprojective spatial pair to the builder.

        .. note::
            This increments the counter by two.

        """
        i = self._i
        name = self.header[f'DWNAME{self.n}']
        name = name.split(' ')[0]
        axes_names = [(self.header[f'DWNAME{nn}'].rsplit(' ')[1]) for nn in (self.n, self._n(i+1))]

        obstime = Time(self.header['DATE-BGN'])
        axes_types = ["lat" if "LT" in self.axes_types[i] else "lon", "lon" if "LN" in self.axes_types[i] else "lat"]
        self._frames.append(cf.CelestialFrame(axes_order=(i, i+1), name=name,
                                              reference_frame=Helioprojective(obstime=obstime),
                                              axes_names=axes_names,
                                              unit=self.get_units(self._i, self._i+1),
                                              axis_physical_types=(f"custom:pos.helioprojective.{axes_types[0]}",
                                                                   f"custom:pos.helioprojective.{axes_types[1]}")))

        self._transforms.append(spatial_model_from_header(self.header))

        self._i += 2

    def make_spectral(self):
        """
        Decide how to make a spectral axes.
        """
        name = self.header[f'DWNAME{self.n}']
        self._frames.append(cf.SpectralFrame(axes_order=(self._i,),
                                             axes_names=(name,),
                                             unit=self.get_units(self._i),
                                             name=name))

        if "WAVE" in self.header.get(f'CTYPE{self.n}', ''):
            transform = self.make_spectral_from_wcs()
        elif "FRAMEWAV" in self.header.keys():
            transform = self.make_spectral_from_dataset()
        else:
            raise ValueError("Could not parse spectral WCS information from this header.")  # pragma: no cover

        self._transforms.append(transform)

        self._i += 1

    def make_spectral_from_dataset(self):
        """
        Make a spectral axes from (VTF) dataset info.
        """
        framewave = [h['FRAMEWAV'] for h in self.slice_headers[:self.header[f'DNAXIS{self.n}']]]
        return spectral_model_from_framewave(framewave)

    def make_spectral_from_wcs(self):
        """
        Add a spectral axes from the FITS-WCS keywords.
        """
        return linear_spectral_model(self.header[f'CDELT{self.n}']*u.nm,
                                     self.header[f'CRVAL{self.n}']*u.nm)
