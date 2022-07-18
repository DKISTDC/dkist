"""
This module contains mitigation's for some known data caveats.
"""
from ndcube.wcs.wrappers.reordered_wcs import ReorderedLowLevelWCS

import dkist


def swap_world_axes(dataset: dkist.Dataset, axis1: int, axis2: int) -> dkist.Dataset:
    """
    This function swaps the position of two world axes.

    Given a dataset and two world axes numbers (zero indexed) swap the positions of those two world axes in the dataset.

    Parameters
    ----------
    dataset
        The dataset to swap the world axes in.
    axis1
        The first world axis to swap
    axis2
        The second world axis to swap

    Returns
    -------
    dataset
        A new dataset object with an updated WCS with the world axes in a different order.

    Notes
    -----
    This function changes the type ``.wcs`` property of the WCS from the
    `gwcs.WCS` object to a
    `~ndcube.wcs.wrappers.reordered_wcs.ReorderedLowLevelWCS` object.
    """
    world_order = list(range(dataset.wcs.world_n_dim))
    new_world_order = list(range(dataset.wcs.world_n_dim))

    new_world_order[axis1] = world_order[axis2]
    new_world_order[axis2] = world_order[axis1]

    pixel_order = list(range(dataset.wcs.pixel_n_dim))
    new_wcs = ReorderedLowLevelWCS(dataset.wcs, pixel_order, new_world_order)
    new_dataset = dkist.Dataset(dataset.data,
                                wcs=new_wcs,
                                uncertainty=dataset.uncertainty,
                                mask=dataset.mask,
                                meta=dataset.meta,
                                unit=dataset.unit,
                                copy=False)
    new_dataset._file_manager = dataset._file_manager

    return new_dataset
