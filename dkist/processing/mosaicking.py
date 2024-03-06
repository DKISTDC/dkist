"""
Helper functions for stitching (VBI) frames.
"""

import copy
from typing import Callable

import numpy as np
import reproject
import reproject.mosaicking
import tqdm

import astropy.units as u
from astropy.table import Table
from gwcs import WCS
from gwcs import coordinate_frames as cf

import dkist


def _unify_output_frames(tds: dkist.TiledDataset, reference_tile: tuple[slice]):
    """
    Given a `dkist.TiledDataset` return a new version where all the WCSes share
    the same celestial output frame.
    """
    ref_wcs = tds[reference_tile].wcs
    ref_celestial_frame = [f for f in ref_wcs.output_frame.frames if isinstance(f, cf.CelestialFrame)][0]
    new_datasets = []
    for ds in tds.flat:
        celestial_ind = int(np.where([isinstance(f, cf.CelestialFrame) for f in ds.wcs.output_frame.frames])[0][0])
        new_frames = copy.deepcopy(ds.wcs.output_frame.frames)
        new_frames[celestial_ind] = ref_celestial_frame
        new_wcs = WCS(
            ds.wcs.forward_transform,
            input_frame=ds.wcs.input_frame,
            output_frame=cf.CompositeFrame(new_frames),
        )
        new_ds = dkist.Dataset(
            ds.data,
            new_wcs,
            meta=ds.meta,
            unit=ds.unit,
            mask=ds.mask,
        )
        new_ds._file_manager = ds._file_manager
        new_datasets.append(new_ds)

    return dkist.TiledDataset(
        np.array(new_datasets).reshape(tds.shape),
        inventory=tds.inventory,
    )


def reproject_vbi(
    tds: dkist.TiledDataset,
    *,
    edge_crop: int = 50,
    reference_tile: tuple[slice] = np.s_[2, 0],
    reproject_function: Callable,
    roundtrip_coords: bool = False,
    combine_function: str = "first",
    shape_out: tuple[int] = None,
):
    uni_tds = _unify_output_frames(tds, reference_tile)
    cropped = dkist.TiledDataset(
        np.array([ds[:, edge_crop:-edge_crop, edge_crop:-edge_crop] for ds in uni_tds.flat]).reshape(tds.shape),
        inventory=tds.inventory,
    )

    target_shape = shape_out or np.array(cropped[reference_tile][0].data.shape) * cropped.shape

    # We are going to use the reference_tile's WCS to create our output WCS
    ref_tile = tds[reference_tile]
    # Get the model for the celestial coords of the first image in the ref tile
    celestial = ref_tile.wcs.forward_transform[0].transform_at_index(0)
    # We are using the timesteps for the ref tile
    # TODO: use the mean time of all the tiles and align this with obstime in the celestial frame
    temporal = ref_tile.wcs.forward_transform[1]

    target_celestial_wcs = WCS(
        forward_transform=celestial,
        input_frame=cf.CoordinateFrame(2, ["PIXEL", "PIXEL"], (0, 1), unit=(u.pix, u.pix)),
        output_frame=ref_tile.wcs.output_frame.frames[0],
    )

    target_full_wcs = WCS(
        forward_transform=celestial & temporal,
        input_frame=cf.CoordinateFrame(3, ["PIXEL"]*3, (0, 1, 2), unit=[u.pix]*3),
        output_frame=ref_tile.wcs.output_frame,
    )

    output = []
    footprint = []
    for tind in tqdm.tqdm(range(uni_tds.flat[0].data.shape[0])):
        tiles = [ds[tind] for ds in cropped.flat]
        arr, fp = reproject.mosaicking.reproject_and_coadd(
            tiles,
            target_celestial_wcs,
            shape_out=target_shape,
            reproject_function=reproject_function,
            roundtrip_coords=roundtrip_coords,
            combine_function=combine_function,
        )
        output.append(arr)
        footprint.append(fp)

    output = np.array(output)
    footprint = np.array(footprint)

    new_ds = dkist.Dataset(
        output,
        wcs=target_full_wcs,
        unit=ref_tile.unit,
        # TODO: hmm?
        meta={"headers": Table(), "inventory": tds.inventory},
    )

    return new_ds, footprint
