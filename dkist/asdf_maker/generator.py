import pathlib

import numpy as np

import asdf
import gwcs
import astropy.units as u
import gwcs.coordinate_frames as cf
from astropy.io import fits
from astropy.time import Time
from astropy.table import Table
from gwcs.lookup_table import LookupTable
from sunpy.coordinates import Helioprojective

from dkist.asdf_maker.helpers import (linear_spectral_model, time_model_from_date_obs,
                                      references_from_filenames, spatial_model_from_header,
                                      spectral_model_from_framewave)

__all__ = ['dataset_from_fits', 'asdf_tree_from_filenames', 'gwcs_from_headers', 'TransformBuilder',
           'build_pixel_frame', 'validate_headers', 'table_from_headers',
           'headers_from_filenames']


def headers_from_filenames(filenames, hdu=0):
    """
    A generator to get the headers from filenames.
    """
    return [fits.getheader(fname, hdu=hdu) for fname in filenames]


def table_from_headers(headers):
    h0 = headers[0]

    t = Table(list(zip(h0.values())), names=list(h0.keys()))

    for h in headers[1:]:
        t.add_row(h)

    return t


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
    t = table_from_headers(headers)

    """
    Let's do roughly the minimal amount of verification here.
    """

    # For some keys all the values must be the same
    same_keys = ['NAXIS', 'DNAXIS']
    naxis_same_keys = ['NAXISn', 'CTYPEn', 'CRVALn']  # 'CRPIXn'
    dnaxis_same_keys = ['DNAXISn', 'DTYPEn', 'DPNAMEn', 'DWNAMEn']
    # Expand n in NAXIS keys
    for nsk in naxis_same_keys:
        for naxis in range(1, t['NAXIS'][0] + 1):
            same_keys.append(nsk.replace('n', str(naxis)))
    # Expand n in DNAXIS keys
    for dsk in dnaxis_same_keys:
        for dnaxis in range(1, t['DNAXIS'][0] + 1):
            same_keys.append(dsk.replace('n', str(dnaxis)))

    validate_t = t[same_keys]

    for col in validate_t.columns.values():
        if not all(col == col[0]):
            raise ValueError(f"The {col.name} values did not all match:\n {col}")

    return headers


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
    axes_types = [header[f'DTYPE{n}'] for n in range(1, header['DNAXIS'] + 1)]

    return cf.CoordinateFrame(naxes=header['DNAXIS'],
                              axes_type=axes_types,
                              axes_order=range(header['DNAXIS']),
                              unit=[u.pixel]*header['DNAXIS'],
                              axes_names=[header[f'DPNAME{n}'] for n in range(1, header['DNAXIS'] + 1)],
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
        return self._n(self._i)

    def _n(self, i):
        """
        Convert a Python index ``i`` to a FITS order index for keywords ``n``.
        """
        # return range(self.header['DNAXIS'], 0, -1)[i]
        return i + 1

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
        self._transforms.append(LookupTable([0, 1, 2, 3] * u.pixel))

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
        name = self.header[f'DWNAME{self.n}']
        name = name.split(' ')[0]
        axes_names = [(self.header[f'DWNAME{nn}'].rsplit(' ')[1]) for nn in (self.n, self._n(i+1))]

        obstime = Time(self.header['DATE-BGN'])
        self._frames.append(cf.CelestialFrame(axes_order=(i, i+1), name=name,
                                              reference_frame=Helioprojective(obstime=obstime),
                                              axes_names=axes_names,
                                              unit=self.get_units(self._i, self._i+1)))

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
        framewave = [h['FRAMEWAV'] for h in self.headers[:self.header[f'DNAXIS{self.n}']]]
        return spectral_model_from_framewave(framewave)

    def make_spectral_from_wcs(self):
        """
        Add a spectral axes from the FITS-WCS keywords.
        """
        return linear_spectral_model(self.header[f'CDELT{self.n}']*u.nm,
                                     self.header[f'CRVAL{self.n}']*u.nm)


def gwcs_from_headers(headers):
    """
    Given a list of headers build a gwcs.

    Parameters
    ----------

    headers : `list`
        A list of headers. These are expected to have already been validated.
    """
    # Now we know the headers are consistent, a lot of parts only need the first one.
    header = headers[0]

    pixel_frame = build_pixel_frame(header)

    builder = TransformBuilder(headers)
    world_frame = cf.CompositeFrame(builder.frames)

    return gwcs.WCS(forward_transform=builder.transform,
                    input_frame=pixel_frame,
                    output_frame=world_frame)


def sorter_DINDEX(headers):
    """
    A sorting function based on the values of DINDEX in the header.
    """
    t = table_from_headers(headers)
    dataset_axes = headers[0]['DNAXIS']
    array_axes = headers[0]['DAAXES']
    keys = [f'DINDEX{k}' for k in range(dataset_axes, array_axes, -1)]
    t = np.array(t[keys])
    return np.argsort(t, order=keys)


def asdf_tree_from_filenames(filenames, hdu=0):
    """
    Build a DKIST asdf tree from a list of (unsorted) filenames.

    Parameters
    ----------

    filenames : `list`
        The filenames to process into a DKIST asdf dataset.

    hdu : `int`
        The HDU to read from the FITS files.
    """
    # headers is an iterator
    headers = headers_from_filenames(filenames, hdu=hdu)

    # headers is a now list
    headers = validate_headers(headers)

    # Sort the filenames into DS order.
    sorted_filenames = np.array(filenames)[sorter_DINDEX(headers)]

    # Get the array shape
    shape = tuple((headers[0][f'DNAXIS{n}'] for n in range(headers[0]['DNAXIS'],
                                                           headers[0]['DAAXES'], -1)))

    # References from filenames
    reference_array = references_from_filenames(sorted_filenames, array_shape=shape)

    tree = {'dataset': reference_array,
            'gwcs': gwcs_from_headers(headers)}

    # TODO: Write a schema for the tree.

    return tree


def dataset_from_fits(path, asdf_filename, hdu=0):
    """
    Given a path containing FITS files write an asdf file in the same path.

    Parameters
    ----------
    path : `pathlib.Path` or `str`
        The path to read the FITS files (with a `.fits` file extension) from and save the asdf file.

    asdf_filename : `str`
        The filename to save the asdf with in the path.

    hdu : `int`
        The HDU to read from the FITS files.

    """
    path = pathlib.Path(path)

    files = path.glob("*fits")

    tree = asdf_tree_from_filenames(list(files), hdu=hdu)

    with asdf.AsdfFile(tree) as afile:
        afile.write_to(str(path/asdf_filename))
