import os
import pathlib

import numpy as np

import asdf
from astropy.io.fits.hdu.base import BITPIX2DTYPE

from dkist.asdf_maker.helpers import headers_from_filenames, preprocess_headers
from dkist.asdf_maker.simulated_data import generate_datset_inventory_from_headers
from dkist.asdf_maker.transforms import TransformBuilder
from dkist.dataset import Dataset
from dkist.io import AstropyFITSLoader, DaskFITSArrayContainer

try:
    from importlib import resources  # >= py 3.7
except ImportError:
    import importlib_resources as resources


__all__ = ['references_from_filenames', 'dataset_from_fits', 'asdf_tree_from_filenames']


def references_from_filenames(filenames, headers, array_shape, hdu_index=0, relative_to=None):
    """
    Given an array of paths to FITS files create a `dkist.io.DaskFITSArrayContainer`.

    Parameters
    ----------
    filenames : `numpy.ndarray`
        An array of filenames, in numpy order for the output array (i.e. ``.flat``)

    headers : `list`
        A list of headers for files

    array_shape : `tuple`
        The desired output shape of the reference array. (i.e the shape of the
        data minus the HDU dimensions.)

    hdu_index : `int` (optional, default 0)
        The index of the HDU to reference. (Zero indexed)

    relative_to : `str` (optional)
        If set convert the filenames to be relative to this path.

    Returns
    -------
    `dkist.io.DaskFITSArrayContainer`
        A container that represents a set of FITS files, and can generate a `dask.array.Array` from them.
    """

    filenames = np.asanyarray(filenames)
    filepaths = np.empty(array_shape, dtype=object)
    if filenames.size != filepaths.size:
        raise ValueError(f"An incorrect number of filenames ({filenames.size})"
                         f" supplied for array_shape ({array_shape})")

    dtypes = []
    shapes = []
    for i, (filepath, head) in enumerate(zip(filenames.flat, headers.flat)):
        dtypes.append(BITPIX2DTYPE[head['BITPIX']])
        shapes.append(tuple([int(head[f"NAXIS{a}"]) for a in range(head["NAXIS"], 0, -1)]))

        # Convert paths to relative paths
        relative_path = filepath
        if relative_to:
            relative_path = os.path.relpath(filepath, str(relative_to))

        filepaths.flat[i] = str(relative_path)

    # Validate all shapes and dtypes are consistent.
    dtype = set(dtypes)
    if len(dtype) != 1:
        raise ValueError("Not all the dtypes of these files are the same.")
    dtype = list(dtype)[0]

    shape = set(shapes)
    if len(shape) != 1:
        raise ValueError("Not all the shapes of these files are the same")
    shape = list(shape)[0]

    return DaskFITSArrayContainer(filepaths.tolist(), hdu_index, dtype, shape, loader=AstropyFITSLoader)


def asdf_tree_from_filenames(filenames, asdf_filename, inventory=None, hdu=0,
                             relative_to=None, extra_inventory=None):
    """
    Build a DKIST asdf tree from a list of (unsorted) filenames.

    Parameters
    ----------

    filenames : `list`
        The filenames to process into a DKIST asdf dataset.

    hdu : `int`
        The HDU to read from the FITS files.
    """
    # In case filenames is a generator we cast to list.
    filenames = list(filenames)

    # headers is an iterator
    headers = headers_from_filenames(filenames, hdu=hdu)

    table_headers, sorted_filenames, sorted_headers = preprocess_headers(headers, filenames)

    if not inventory:
        inventory = generate_datset_inventory_from_headers(table_headers, asdf_filename)
    if extra_inventory:
        inventory.update(extra_inventory)


    ds_wcs = TransformBuilder(sorted_headers).gwcs

    # Get the array shape
    shape = tuple((headers[0][f'DNAXIS{n}'] for n in range(headers[0]['DNAXIS'],
                                                           headers[0]['DAAXES'], -1)))
    # References from filenames
    array_container = references_from_filenames(sorted_filenames, sorted_headers, array_shape=shape,
                                                hdu_index=hdu, relative_to=relative_to)

    ds = Dataset(array_container.array, ds_wcs, meta=inventory, headers=table_headers)

    ds._array_container = array_container

    tree = {'dataset': ds}

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
            afile.write_to(path / asdf_filename, **kwargs)
