import pytest

from ndcube.wcs.wrappers.reordered_wcs import ReorderedLowLevelWCS

from dkist.processing.caveats import swap_world_axes


@pytest.mark.parametrize("dataset", ("dataset_4d", "eit_dataset"), indirect=True)
def test_swap_world_axes(dataset):
    new_ds = swap_world_axes(dataset, 0, 1)
    assert new_ds.wcs.world_axis_physical_types[0] == dataset.wcs.world_axis_physical_types[1]

    assert new_ds.files is dataset.files
    assert isinstance(new_ds.wcs.low_level_wcs, ReorderedLowLevelWCS)
