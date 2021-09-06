import os
import glob
from pathlib import Path

import numpy as np

import asdf
import astropy.units as u
import gwcs
import sunpy.map
from astropy.io import fits
from astropy.modeling.models import (AffineTransformation2D, Multiply,
                                     Pix2Sky_TAN, RotateNative2Celestial, Shift)
from astropy.time import Time
from gwcs import coordinate_frames as cf
from sunpy.net import Fido
from sunpy.net import attrs as a
from sunpy.net.jsoc import JSOCClient
from sunpy.time import parse_time

from dkist.asdf_maker.helpers import generate_lookup_table


def map_to_transform(smap):
    # crval1u, crval2u = smap.reference_coordinate.Tx, smap.reference_coordinate.Ty
    # cdelt1u, cdelt2u = smap.scale
    # pcu = smap.rotation_matrix * u.arcsec

    # # First, shift the reference pixel from FITS (1) to Python (0) indexing
    # crpix1, crpix2 = u.Quantity(smap.reference_pixel) - 1 * u.pixel
    # # Then FITS WCS uses the negative of this value as the shift.
    # shiftu = Shift(-crpix1) & Shift(-crpix2)

    # # Next we define the Affine Transform.
    # # This also includes the pixel scale operation by using equivalencies
    # scale_e = {a: u.pixel_scale(scale) for a, scale in zip('xy', smap.scale)}
    # rotu = AffineTransformation2D(pcu, translation=(0, 0) * u.arcsec)
    # rotu.input_units_equivalencies = scale_e

    # # Handle the projection
    # tanu = Pix2Sky_TAN()

    # # Rotate from native spherical to celestial spherical coordinates
    # skyrotu = RotateNative2Celestial(crval1u, crval2u, 180 * u.deg)

    # # Combine the whole pipeline into one compound model
    # transu = shiftu | rotu | tanu | skyrotu

    crpix1u, crpix2u = u.Quantity(smap.reference_pixel)-1*u.pixel
    crval1u, crval2u = smap.reference_coordinate.Tx, smap.reference_coordinate.Ty
    cdelt1u, cdelt2u = smap.scale
    pcu = smap.rotation_matrix * u.arcsec
    shiftu = Shift(-crpix1u) & Shift(-crpix2u)
    scaleu = Multiply(cdelt1u) & Multiply(cdelt2u)
    rotu = AffineTransformation2D(pcu, translation=(0, 0)*u.arcsec)
    tanu = Pix2Sky_TAN()
    skyrotu = RotateNative2Celestial(crval1u, crval2u, 180*u.deg)
    transu = shiftu | scaleu | rotu | tanu | skyrotu
    transu.rename("spatial")

    return transu


def references_from_filenames(filename_array, relative_to=None):
    """
    Given an array of paths to FITS files create a set of nested lists of
    `asdf.external_reference.ExternalArrayReference` objects with the same
    shape.
    """

    from asdf.tags.core.external_reference import ExternalArrayReference
    from astropy.io.fits.hdu.base import BITPIX2DTYPE

    reference_array = np.empty_like(filename_array, dtype=object)
    for i, filepath in enumerate(filename_array.flat):
        with fits.open(filepath) as hdul:
            hdu_index = 1
            hdu = hdul[hdu_index]
            dtype = BITPIX2DTYPE[hdu.header['BITPIX']]
            shape = tuple(reversed(hdu.shape))

            # Convert paths to relative paths
            relative_path = filepath
            if relative_to:
                relative_path = os.path.relpath(filepath, relative_to)

            reference_array.flat[i] = ExternalArrayReference(
                relative_path, hdu_index, dtype, shape)

    return reference_array.tolist()


def main():
    path = Path('~/sunpy/data/jsocflare/').expanduser()
    files = glob.glob(str(path / '*.fits'))

    # requestid = 'JSOC_20180831_1097'
    requestid = None

    if not files:
        if requestid:
            c = JSOCClient()
            filesd = c.get_request(
                requestid, path=str(path), overwrite=False).wait()
            files = []
            for f in filesd.values():
                files.append(f['path'])
        else:
            results = Fido.search(
                a.jsoc.Time('2017-09-06T12:00:00', '2017-09-06T12:02:00'),
                a.jsoc.Series('aia.lev1_euv_12s'), a.jsoc.Segment('image'),
                a.jsoc.Notify("stuart@cadair.com"))

            print(results)

            files = Fido.fetch(results, path=str(path))

    files.sort()
    files = np.array(files)

    # For each image get:
    # the index
    inds = []
    # the time
    times = []
    # the dt from the first image
    seconds = []
    # the wavelength
    waves = []

    for i, filepath in enumerate(files):
        with fits.open(filepath) as hdul:
            header = hdul[1].header
        time = parse_time(header['DATE-OBS'])
        if i == 0:
            root_header = header
            start_time = time
        inds.append(i)
        times.append(time)
        seconds.append((time - start_time).total_seconds())
        waves.append(header['WAVELNTH'])

    # Construct an array and sort it by wavelength and time
    arr = np.array((inds, seconds, waves)).T
    sorter = np.lexsort((arr[:, 1], arr[:, 2]))

    # Using this double-sorted array get the list indicies
    list_sorter = np.array(arr[sorter][:, 0], dtype=int)

    # Calculate the desired shape of the output array
    n_waves = len(list(set(waves)))
    shape = (n_waves, len(files) // n_waves)

    # Construct a 2D array of filenames
    cube = files[list_sorter].reshape(shape)

    # Extract a list of coordinates in time and wavelength
    # this assumes all wavelength images are taken at the same time
    time_coords = np.array(
        [t.isoformat() for t in times])[list_sorter].reshape(shape)[0, :]
    wave_coords = np.array(waves)[list_sorter].reshape(shape)[:, 0]

    smap0 = sunpy.map.Map(files[0])
    spatial = map_to_transform(smap0)

    timemodel = generate_lookup_table(lookup_table=seconds[:shape[1]]*u.s)
    wavemodel = generate_lookup_table(lookup_table=waves[:shape[0]]*u.AA)

    hcubemodel = spatial & timemodel & wavemodel

    wave_frame = cf.SpectralFrame(axes_order=(3, ), unit=u.AA, name="wavelength", axes_names=("wavelength", ))
    time_frame = cf.TemporalFrame(
        axes_order=(2, ), unit=u.s, reference_time=Time(time_coords[0]), name="time", axes_names=("time", ))
    sky_frame = cf.CelestialFrame(axes_order=(0, 1), name='helioprojective',
                                  reference_frame=smap0.coordinate_frame,
                                  axes_names=("helioprojective longitude", "helioprojective latitude"))

    sky_frame = cf.CompositeFrame([sky_frame, time_frame, wave_frame])
    detector_frame = cf.CoordinateFrame(name="detector", naxes=4,
                                        axes_order=(0, 1, 2, 3),
                                        axes_type=("pixel", "pixel", "pixel", "pixel"),
                                        axes_names=("x", "y", "time", "wavelength"),
                                        unit=(u.pix, u.pix, u.pix, u.pix))

    wcs = gwcs.wcs.WCS(forward_transform=hcubemodel, input_frame=detector_frame,
                       output_frame=sky_frame)

    print(repr(wcs))

    print(wcs(*[1*u.pix]*4, with_units=True))

    ea = references_from_filenames(cube, relative_to=str(path))

    tree = {
        'gwcs': wcs,
        'dataset': ea,
    }

    with asdf.AsdfFile(tree) as ff:
        # ff.write_to("test.asdf")
        filename = str(path / "aia_{}.asdf".format(time_coords[0]))
        ff.write_to(filename)
        print("Saved to : {}".format(filename))

    # import sys; sys.exit(0)

    from dkist.dataset import Dataset

    ds = Dataset.from_directory(str(path))
    print(repr(ds))
    print(repr(ds.wcs))
    print(ds.wcs(*[1*u.pix]*4, with_units=True))


if __name__ == "__main__":
    main()
