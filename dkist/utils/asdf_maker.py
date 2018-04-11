import os

import asdf
import numpy as np
from astropy.io import fits
from astropy.io.fits.hdu.base import BITPIX2DTYPE
from asdf.tags.core.external_reference import ExternalArrayReference


def references_from_filenames(filenames, array_shape, hdu_index=0, relative_to=None):
    """
    Given an array of paths to FITS files create a set of nested lists of
    `asdf.external_reference.ExternalArrayReference` objects with the same
    shape.

    Parameters
    ----------

    filenames : `numpy.ndarray`
        An array of filenames, in numpy order for the output array (i.e. ``.flat``)

    array_shape : `tuple`
        The desired output shape of the reference array. (i.e the shape of the
        data minus the HDU dimensions.)

    hdu_index : `int` (optional, default 0)
        The index of the HDU to reference. (Zero indexed)

    relative_to : `str` (optional)
        If set convert the filenames to be relative to this path.
    """

    filenames = np.asanyarray(filenames)
    reference_array = np.empty(array_shape, dtype=object)
    for i, filepath in enumerate(filenames.flat):
        with fits.open(filepath) as hdul:
            hdu = hdul[hdu_index]
            dtype = BITPIX2DTYPE[hdu.header['BITPIX']]
            # hdu.shape is already in Python order
            shape = tuple(hdu.shape)

            # Convert paths to relative paths
            relative_path = filepath
            if relative_to:
                relative_path = os.path.relpath(filepath, relative_to)

            reference_array.flat[i] = ExternalArrayReference(
                relative_path, hdu_index, dtype, shape)

    return reference_array.tolist()


def make_asdf(filename, *, dataset, gwcs, **kwargs):
    """
    Save an asdf file.

    All keyword arguments become keys in the top level of the asdf tree.
    """
    tree = {
        'gwcs': gwcs,
        'dataset': dataset,
    }

    with asdf.AsdfFile(tree) as ff:
        ff.write_to(str(filename))

    return filename
