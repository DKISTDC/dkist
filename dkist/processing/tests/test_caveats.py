from dkist.processing.caveats import swap_world_axes


def test_swap_world_axes(dataset_4d):
    new_ds = swap_world_axes(dataset_4d, 1, 2)
    assert new_ds.wcs.world_axis_physical_types[1] == dataset_4d.wcs.world_axis_physical_types[2]
