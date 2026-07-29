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
    from dkist.dataset import TiledDataset  # noqa: PLC0415

    is_tiled = isinstance(ds_in, TiledDataset)
    dstype = type(ds_in).__name__
    if is_tiled:
        tile_shape = ds_in.shape
        # Not using .flat here for performance reasons
        ds = ds_in._data.compressed()[0]
    else:
        ds = ds_in
    wcs = ds.wcs.low_level_wcs

    # Array dimensions table

    instr = ds.inventory.get("instrumentName", "")
    if instr:
        instr += " "
    pID = ds.inventory.get("productId", "(no ProductID)")
    dsID = ds.inventory.get("datasetId", "(no DatasetID)")

    s = f"This {instr}Dataset "
    if is_tiled:
        s += f"is an array of {tile_shape} Dataset objects "
        if ds.files:
            s += "and \n"

    if ds.files:
        # Not using .flat here for performance reasons
        nframes = len(ds.files) if not is_tiled else sum([len(tile.files) for tile in ds_in._data.compressed()])
        s += f"consists of {nframes} frames.\n"
        s += f"Files are stored in {ds.files.basepath}\n"

    s += f"\nThis calibration has Dataset ID {dsID}."
    s += f"\nThe unique identifier for the input observe frames (Product ID) is {pID}.\n"

    if is_tiled:
        s += "\nEach "
    else:
        s += "\nThis "
    s += f"Dataset has {wcs.pixel_n_dim} pixel and {wcs.world_n_dim} world dimensions.\n\n"

    s += f"The data are represented by a {type(ds.data)} object:\n{get_array_repr(ds.data)}\n\n"

    s += array_dimensions_info(wcs)
    s += world_dimensions_info(wcs)

    # Axis correlation matrix
    pixel_dim_width = max(3, len(str(wcs.world_n_dim)))
    s += "Correlation between pixel and world axes:\n\n"
    s += _get_pp_matrix(ds.wcs)

    # Make sure we get rid of the extra whitespace at the end of some lines
    return "\n".join([line.rstrip() for line in s.splitlines()])


def inversion_info_str(inv_in):
    s = f"This Level 2 product is a dictionary of {len(inv_in.items())} Datasets with {len(inv_in.aligned_dimensions)} aligned dimensions "
    s += f"and consists of {sum([len(ds.files._fm.filenames) for ds in inv_in.values()])} total frames.\n"
    basepaths = []
    for ds in inv_in.values():
        basepaths.append(ds.files.basepath)
    basepaths = set(basepaths)
    if len(basepaths) == 1:
        s += f"Files are stored in {list(basepaths)[0]}\n"
    else:
        s += "Files are stored in the following locations:\n"
        for path in basepaths:
            s += f"- {path}\n"

    s += "\nThis Inversion has ID ...\n\n"

    s += f"The Datasets in this Inversion represent the following {len(inv_in.items())} physical parameters:\n"
    for param in inv_in.keys():
        s += f"- {param}\n"

    lines = []
    for p in inv_in.profiles.keys():
        line = p[:p.index("_")] if "_" in p else p
        if line not in lines:
            lines.append(line)
    s += f"\nThese parameters were calculated using the following {len(lines)} line profiles "
    s += "(see the .profiles attribute for more information) :\n"
    for line in lines:
        s += f"- {line}\n"
    s += "\n"

    # This section shows only info about the pixel axes shared across all inversions and the
    # corresponding world axes
    s += "The following information relates to only the pixel axes shared by all inversions, and the\n"
    s += "corresponding world axes. Invdividual inversions may include other coordinate information.\n"
    aligned_axes = list(inv_in.aligned_axes.values())
    indices = list(set(aligned_axes[0]).intersection(*aligned_axes))
    # Low level Just in case the dataset has been sliced and returned the wrong kind of wcs
    wcs = inv_in[list(inv_in.keys())[0]].wcs.low_level_wcs
    s += array_dimensions_info(wcs, indices)
    s += world_dimensions_info(wcs, indices)

    # Axis correlation matrix
    pixel_dim_width = max(3, len(str(wcs.world_n_dim)))
    s += "Correlation between pixel and world axes:\n\n"
    s += _get_pp_matrix(ds.wcs, indices)


    # Make sure we get rid of the extra whitespace at the end of some lines
    return "\n".join([line.rstrip() for line in s.splitlines()])


def array_dimensions_info(wcs, indices=None):
    n_dim = len(indices) if indices else wcs.pixel_n_dim
    indices = indices if indices else range(wcs.pixel_n_dim)
    array_shape = wcs.array_shape or (0,)
    pixel_shape = wcs.pixel_shape or (None,) * n_dim

    # Find largest between header size and value length
    if hasattr(wcs, "pixel_axis_names"):
        pixel_axis_names = [wcs.pixel_axis_names[i] for i in indices]
    elif isinstance(wcs, gwcs.WCS):
        pixel_axis_names = [wcs.input_frame.axes_names[i] for i in indices]
    else:
        pixel_axis_names = [""] * n_dim

    pixel_dim_width = max(9, len(str(n_dim)))
    pixel_nam_width = max(9, max(len(x) for x in pixel_axis_names))
    pixel_siz_width = max(9, len(str(max(array_shape))))

    s = (("{0:" + str(pixel_dim_width) + "s}").format("Array Dim") + "  " +
           ("{0:" + str(pixel_nam_width) + "s}").format("Axis Name") + "  " +
           ("{0:" + str(pixel_siz_width) + "s}").format("Data size") + "  " +
           "Bounds\n")

    for ipix in range(n_dim):
        s += (("{0:" + str(pixel_dim_width) + "d}").format(ipix) + "  " +
                ("{0:" + str(pixel_nam_width) + "s}").format(pixel_axis_names[::-1][ipix] or "None") + "  " +
                (" " * 5 + str(None) if pixel_shape[::-1][ipix] is None else
                ("{0:" + str(pixel_siz_width) + "d}").format(pixel_shape[::-1][ipix])) + "  " +
                "{:s}".format(str(None if wcs.pixel_bounds is None else wcs.pixel_bounds[::-1][ipix]) + "\n"))
    s += "\n"

    return s


def world_dimensions_info(wcs, indices=None):
    acm = wcs.axis_correlation_matrix
    if indices:
        acm = acm[:, indices]
    n_dim = len(indices) if indices else wcs.pixel_n_dim
    indices = indices if indices else range(wcs.pixel_n_dim)
    # Find largest between header size and value length
    world_dim_width = max(9, len(str(n_dim)))
    world_nam_width = max(9, max(len(x) if x is not None else 0 for x in [wcs.world_axis_names[i] for i in indices]))
    world_typ_width = max(13, max(len(x) if x is not None else 0 for x in [wcs.world_axis_physical_types[i] for i in indices]))

    s = (("{0:" + str(world_dim_width) + "s}").format("World Dim") + "  " +
           ("{0:" + str(world_nam_width) + "s}").format("Axis Name") + "  " +
           ("{0:" + str(world_typ_width) + "s}").format("Physical Type") + "  " +
           "Units\n")

    shared_world_axis_idxs = np.where(np.any(acm, axis=1))[0]
    for iwrl in shared_world_axis_idxs[::-1]:
        name = wcs.world_axis_names[iwrl] or "None"
        typ = wcs.world_axis_physical_types[iwrl] or "None"
        unit = wcs.world_axis_units[iwrl] or "unknown"

        s += (("{0:" + str(world_dim_width) + "d}").format(iwrl) + "  " +
                ("{0:" + str(world_nam_width) + "s}").format(name) + "  " +
                ("{0:" + str(world_typ_width) + "s}").format(typ) + "  " +
                "{:s}".format(unit + "\n"))

    s += "\n"

    return s


def _get_pp_matrix(wcs, indices=None):
    wcs = wcs.low_level_wcs
    acm = wcs.axis_correlation_matrix
    if indices:
        acm = acm[:, indices]
    indices = indices if indices else range(wcs.pixel_n_dim)
    world_indices = np.where(np.any(acm, axis=1))[0]
    acm = acm[world_indices]
    pixel_names = [wcs.pixel_axis_names[i] for i in indices]
    world_names = [wcs.world_axis_names[i] for i in world_indices]
    slen = np.max([len(line) for line in list(world_names) + list(pixel_names)])
    mstr = acm.astype("<U")
    mstr[np.where(mstr == "True")] = "x"
    mstr[np.where(mstr == "False")] = ""
    mstr = mstr.astype(f"<U{slen}")

    labels = pixel_names
    width = max(max([len(w) for w in label.split(" ")]) for label in labels)
    wrapped = [textwrap.wrap(l, width=width, break_long_words=False) for l in labels]
    maxlines = max([len(l) for l in wrapped])
    for l in wrapped:
        while len(l) < maxlines:
            l.append("")
    header = np.vstack([[s.center(width) for s in wrapped[l]] for l, _ in enumerate(labels)]).T

    mstr = np.insert(mstr, 0, header, axis=0)
    world = ["WORLD DIMENSIONS", *world_names]
    nrows = maxlines + len(world_names)
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
    header = (" "*widths[0]) + " | " + "PIXEL DIMENSIONS".center(wid+(3*(len(pixel_names)-1))) + "\n"

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
