import pytest

from dkist.data.test import rootdir


@pytest.fixture(params=[
                        rootdir / "eit_dataset-0.1.0.asdf",
                        rootdir / "eit_dataset-0.2.0.asdf",
                        rootdir / "eit_dataset-0.3.0.asdf",
                        rootdir / "eit_dataset-1.0.0.asdf",
                        rootdir / "eit_dataset-1.1.0.asdf",
                        rootdir / "eit_dataset-1.2.0.asdf",
])
def eit_dataset_asdf_path(request):
    return request.param


@pytest.fixture(params=[
                        rootdir / "test_tiled_dataset-1.0.0_dataset-1.0.0.asdf",
                        rootdir / "test_tiled_dataset-1.0.0_dataset-1.1.0.asdf",
])
def tiled_dataset_asdf_path(request):
    return request.param
