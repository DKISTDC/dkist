"""
Helper functions for the Dataset class.
"""

import textwrap

import numpy as np

import gwcs

__all__ = ["dataset_info_str"]


def get_array_repr(array):
    """
    Return a "repr-like" string for an array, without any values.

    The objective of this function is primarily to provide a dask array like repr for numpy arrays.
    """
    if isinstance(array, np.ndarray):
        return f"numpy.ndarray<shape={array.shape}, dtype={array.dtype}>"
    return repr(array)


def dataset_info_str(ds_in):
    # Import here to remove circular import
    from dkist.dataset import TiledDataset
    is_tiled = isinstance(ds_in, TiledDataset)
    dstype = type(ds_in).__name__
    if is_tiled:
        tile_shape = ds_in.shape
        ds = ds_in.flat[0]
    else:
        ds = ds_in
    wcs = ds.wcs.low_level_wcs

    # Array dimensions table

    instr = ds.inventory.get("instrumentName", "")
    if instr:
        instr += " "
    dsID = ds.inventory.get("datasetId", "(no DatasetID)")

    s = f"This {instr}Dataset {dsID} "
    if is_tiled:
        s += f"is an array of {tile_shape} Dataset objects "
        if ds.files:
            s += "and \n"


    if ds.files:
        nframes = len(ds.files) if not is_tiled else sum([len(tile.files) for tile in ds_in.flat])
        s += f"consists of {nframes} frames.\n"
        s += f"Files are stored in {ds.files.basepath}\n"

    if is_tiled:
        s += "\nEach "
    else:
        s += "\nThis "
    s += f"Dataset has {wcs.pixel_n_dim} pixel and {wcs.world_n_dim} world dimensions.\n\n"

    s += f"The data are represented by a {type(ds.data)} object:\n{get_array_repr(ds.data)}\n\n"

    array_shape = wcs.array_shape or (0,)
    pixel_shape = wcs.pixel_shape or (None,) * wcs.pixel_n_dim

    # Find largest between header size and value length
    if hasattr(wcs, "pixel_axis_names"):
        pixel_axis_names = wcs.pixel_axis_names
    elif isinstance(wcs, gwcs.WCS):
        pixel_axis_names = wcs.input_frame.axes_names
    else:
        pixel_axis_names = [""] * wcs.pixel_n_dim

    pixel_dim_width = max(9, len(str(wcs.pixel_n_dim)))
    pixel_nam_width = max(9, max(len(x) for x in pixel_axis_names))
    pixel_siz_width = max(9, len(str(max(array_shape))))

    s += (("{0:" + str(pixel_dim_width) + "s}").format("Array Dim") + "  " +
            ("{0:" + str(pixel_nam_width) + "s}").format("Axis Name") + "  " +
            ("{0:" + str(pixel_siz_width) + "s}").format("Data size") + "  " +
            "Bounds\n")

    for ipix in range(ds.wcs.pixel_n_dim):
        s += (("{0:" + str(pixel_dim_width) + "d}").format(ipix) + "  " +
                ("{0:" + str(pixel_nam_width) + "s}").format(pixel_axis_names[::-1][ipix] or "None") + "  " +
                (" " * 5 + str(None) if pixel_shape[::-1][ipix] is None else
                ("{0:" + str(pixel_siz_width) + "d}").format(pixel_shape[::-1][ipix])) + "  " +
                "{:s}".format(str(None if wcs.pixel_bounds is None else wcs.pixel_bounds[::-1][ipix]) + "\n"))
    s += "\n"

    # World dimensions table

    # Find largest between header size and value length
    world_dim_width = max(9, len(str(wcs.world_n_dim)))
    world_nam_width = max(9, max(len(x) if x is not None else 0 for x in wcs.world_axis_names))
    world_typ_width = max(13, max(len(x) if x is not None else 0 for x in wcs.world_axis_physical_types))

    s += (("{0:" + str(world_dim_width) + "s}").format("World Dim") + "  " +
            ("{0:" + str(world_nam_width) + "s}").format("Axis Name") + "  " +
            ("{0:" + str(world_typ_width) + "s}").format("Physical Type") + "  " +
            "Units\n")

    for iwrl in range(wcs.world_n_dim)[::-1]:

        name = wcs.world_axis_names[iwrl] or "None"
        typ = wcs.world_axis_physical_types[iwrl] or "None"
        unit = wcs.world_axis_units[iwrl] or "unknown"

        s += (("{0:" + str(world_dim_width) + "d}").format(iwrl) + "  " +
                ("{0:" + str(world_nam_width) + "s}").format(name) + "  " +
                ("{0:" + str(world_typ_width) + "s}").format(typ) + "  " +
                "{:s}".format(unit + "\n"))

    s += "\n"

    # Axis correlation matrix

    pixel_dim_width = max(3, len(str(wcs.world_n_dim)))

    s += "Correlation between pixel and world axes:\n\n"

    s += _get_pp_matrix(ds.wcs)

    # Make sure we get rid of the extra whitespace at the end of some lines
    return "\n".join([line.rstrip() for line in s.splitlines()])


def _get_pp_matrix(wcs):
    wcs = wcs.low_level_wcs # Just in case the dataset has been sliced and returned the wrong kind of wcs
    slen = np.max([len(line) for line in list(wcs.world_axis_names) + list(wcs.pixel_axis_names)])
    mstr = wcs.axis_correlation_matrix.astype("<U")
    mstr[np.where(mstr == "True")] = "x"
    mstr[np.where(mstr == "False")] = ""
    mstr = mstr.astype(f"<U{slen}")

    labels = wcs.pixel_axis_names
    width = max(max([len(w) for w in label.split(" ")]) for label in labels)
    wrapped = [textwrap.wrap(l, width=width, break_long_words=False) for l in labels]
    maxlines = max([len(l) for l in wrapped])
    for l in wrapped:
        while len(l) < maxlines:
            l.append("")
    header = np.vstack([[s.center(width) for s in wrapped[l]] for l, _ in enumerate(labels)]).T

    mstr = np.insert(mstr, 0, header, axis=0)
    world = ["WORLD DIMENSIONS", *list(wcs.world_axis_names)]
    nrows = maxlines + len(wcs.world_axis_names)
    while len(world) < nrows:
        world.insert(0, "")
    mstr = np.insert(mstr, 0, world, axis=1)
    widths = [np.max([len(a) for a in col]) for col in mstr.T]
    mstr = np.insert(mstr, header.shape[0], ["-"*wid for wid in widths], axis=0)
    for i, col in enumerate(mstr.T):
        if i == 0:
            mstr[:, i] = np.char.rjust(col, widths[i])
        else:
            mstr[:, i] = np.char.center(col, widths[i])

    mstr = np.array_str(mstr, max_line_width=1000)
    # Make the matrix string prettier for this context by stripping out the array presentation
    # Probably a nicer way to do this with regexes but this works fine
    mstr = mstr.replace("[[", "").replace(" [", "").replace("]", "").replace("' '", " | ").replace("'", "")
    wid = sum(widths[1:])
    header = (" "*widths[0]) + " | " + "PIXEL DIMENSIONS".center(wid+(3*(len(wcs.pixel_axis_names)-1))) + "\n"

    return header + mstr


def pp_matrix(wcs):
    """
    A small helper function to print a correlation matrix with labels

    Parameters
    ----------
    wcs : `BaseHighLevelWCS` or `BaseLowLevelWCS`
    """
    print(_get_pp_matrix(wcs))  # noqa: T201


def extract_pc_matrix(headers, naxes=None):
    """
    Given an astropy table of headers extract one or more PC matrices.
    """
    if naxes is None:
        naxes = headers[0]["NAXIS"]
    keys = []
    for i, j in np.ndindex((naxes, naxes)):
        keys.append(f"PC{i+1}_{j+1}")

    sub = headers[keys]

    return np.array(np.array(headers[keys]).tolist()).reshape(len(sub), naxes, naxes)
