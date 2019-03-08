import random
import string
import pathlib

import numpy as np

import asdf
import astropy.units as u
import gwcs
import gwcs.coordinate_frames as cf
from astropy.io import fits
from astropy.table import Table
from astropy.time import Time
from gwcs.lookup_table import LookupTable
from sunpy.coordinates import Helioprojective
from sunpy.time import parse_time

from dkist.asdf_maker.helpers import (linear_spectral_model, references_from_filenames,
                                      spatial_model_from_header, spectral_model_from_framewave,
                                      time_model_from_date_obs)

try:
    from importlib import resources  # >= py 3.7
except ImportError:
    import importlib_resources as resources

__all__ = ['generate_datset_inventory_from_headers', 'dataset_from_fits',
           'asdf_tree_from_filenames', 'gwcs_from_headers', 'TransformBuilder',
           'build_pixel_frame', 'validate_headers', 'table_from_headers',
           'headers_from_filenames']


def headers_from_filenames(filenames, hdu=0):
    """
    A generator to get the headers from filenames.
    """
    return [dict(fits.getheader(fname, ext=hdu)) for fname in filenames]


def table_from_headers(headers):
    return Table(rows=headers, names=list(headers[0].keys()))


def validate_headers(table_headers):
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
    t = table_headers

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

    return table_headers


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
        self.header = headers[0]

        # Reshape the headers to match the Dataset shape, so we can extract headers along various axes.
        shape = tuple((self.header[f'DNAXIS{n}'] for n in range(self.header['DNAXIS'],
                                                                self.header['DAAXES'], -1)))
        arr_headers = np.empty(shape, dtype=object)
        for i in range(arr_headers.size):
            arr_headers.flat[i] = headers[i]

        self.headers = arr_headers
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
        framewave = [h['FRAMEWAV'] for h in self.slice_headers[:self.header[f'DNAXIS{self.n}']]]
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
    header = headers[0]

    pixel_frame = build_pixel_frame(header)

    builder = TransformBuilder(headers)
    world_frame = cf.CompositeFrame(builder.frames)

    return gwcs.WCS(forward_transform=builder.transform,
                    input_frame=pixel_frame,
                    output_frame=world_frame)


def make_sorted_table(headers, filenames):
    """
    Return an `astropy.table.Table` instance where the rows are correctly sorted.
    """
    theaders = table_from_headers(headers)
    theaders['filenames'] = filenames
    theaders['headers'] = headers
    dataset_axes = headers[0]['DNAXIS']
    array_axes = headers[0]['DAAXES']
    keys = [f'DINDEX{k}' for k in range(dataset_axes, array_axes, -1)]
    t = np.array(theaders[keys])
    return theaders[np.argsort(t, order=keys)]


def asdf_tree_from_filenames(filenames, asdf_filename, inventory=None, hdu=0, relative_to=None):
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

    table_headers = make_sorted_table(headers, filenames)

    validate_headers(table_headers)

    # Sort the filenames into DS order.
    sorted_filenames = np.array(table_headers['filenames'])
    sorted_headers = np.array(table_headers['headers'])

    table_headers.remove_columns(["headers", "filenames"])

    # Get the array shape
    shape = tuple((headers[0][f'DNAXIS{n}'] for n in range(headers[0]['DNAXIS'],
                                                           headers[0]['DAAXES'], -1)))
    # References from filenames
    reference_array = references_from_filenames(sorted_filenames, sorted_headers, array_shape=shape,
                                                hdu_index=hdu, relative_to=relative_to)

    tree = {'data': reference_array,
            'wcs': gwcs_from_headers(sorted_headers),
            'headers': table_headers,
            'meta': generate_datset_inventory_from_headers(table_headers, asdf_filename)}

    return tree


def dataset_from_fits(path, asdf_filename, inventory=None, hdu=0, relative_to=None, **kwargs):
    """
    Given a path containing FITS files write an asdf file in the same path.

    Parameters
    ----------
    path : `pathlib.Path` or `str`
        The path to read the FITS files (with a `.fits` file extension) from
        and save the asdf file.

    asdf_filename : `str`
        The filename to save the asdf with in the path.

    inventory : `dict`, optional
        The dataset inventory for this collection of FITS. If `None` a random one will be generated.

    hdu : `int`, optional
        The HDU to read from the FITS files.

    relative_to: `pathlib.Path` or `str`, optional
        The base path to use in the asdf references.

    kwargs
        Additional kwargs are passed to `asdf.AsdfFile.write_to`.

    """
    path = pathlib.Path(path)

    files = path.glob("*fits")

    tree = asdf_tree_from_filenames(list(files), asdf_filename, inventory=inventory,
                                    hdu=hdu, relative_to=relative_to)

    with resources.path("dkist.io", "level_1_dataset_schema.yaml") as schema_path:
        with asdf.AsdfFile(tree, custom_schema=schema_path.as_posix()) as afile:
            afile.write_to(path/asdf_filename, **kwargs)


def _gen_type(gen_type, max_int=1e6, max_float=1e6, len_str=30):
    if gen_type is bool:
        return bool(random.randint(0, 1))
    elif gen_type is int:
        return random.randint(0, max_int)
    elif gen_type is float:
        return random.random() * max_float
    elif gen_type is list:
        return [_gen_type(str)]
    elif gen_type is Time:
        return parse_time("now")
    elif gen_type is str:
        return ''.join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(len_str))
    else:
        raise ValueError("Type {} is not supported".format(gen_type))  # pragma: no cover


def generate_datset_inventory_from_headers(headers, asdf_name):
    """
    Generate a dummy dataset inventory from headers.

    .. note::
       This is just for test data, it should not be used on real data.

    Parameters
    ----------

    headers: `astropy.table.Table`
    asdf_name: `str`

    """

    schema = [
        ('asdf_object_key', str),
              ('browse_movie_object_key', str),
              ('browse_movie_url', str),
              ('bucket', str),
              ('contributing_experiment_ids', list),
              ('contributing_proposal_ids', list),
              ('dataset_id', str),
              ('dataset_inventory_id', int),
              ('dataset_size', int),
              ('end_time', Time),
              ('exposure_time', float),
              ('filter_wavelengths', list),
              ('frame_count', int),
              ('has_all_stokes', bool),
              ('instrument_name', str),
              ('observables', list),
              ('original_frame_count', int),
              ('primary_experiment_id', str),
              ('primary_proposal_id', str),
              ('quality_average_fried_parameter', float),
              ('quality_average_polarimetric_accuracy', float),
              ('recipe_id', int),
              ('recipe_instance_id', int),
              ('recipe_run_id', int),
              ('start_time', Time),
              # ('stokes_parameters', str),
              ('target_type', str),
              ('wavelength_max', float),
              ('wavelength_min', float)]

    header_mapping = {
        'start_time': 'DATE-BGN',
        'end_time': 'DATE-END',
        'filter_wavelengths': 'WAVELNGTH'}

    output = {}

    for key, ktype in schema:
        if key in header_mapping:
            hdict = dict(zip(headers.colnames, headers[0]))
            output[key] = ktype(hdict.get(header_mapping[key], _gen_type(ktype)))
        else:
            output[key] = _gen_type(ktype)

    return output
