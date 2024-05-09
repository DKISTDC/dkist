import matplotlib.pyplot as plt
import pytest

from dkist import load_dataset


@pytest.mark.benchmark
def test_load_asdf(benchmark, large_visp_dataset_file):
    benchmark(load_dataset, large_visp_dataset_file)


@pytest.mark.benchmark
@pytest.mark.parametrize("axes", [
    ["y", "x", None, None],
    ["y", None, "x", None],
    ["y", None, None, "x"],
    [None, "y", "x", None],
    [None, "y", None, "x"],
    [None, None, "y", "x"],
])
def test_plot_dataset(benchmark, axes, large_visp_dataset):
    @benchmark
    def plot_and_save_fig(ds=large_visp_dataset, axes=axes):
        ds.plot(plot_axes=axes)
        plt.savefig("tmpplot")
        plt.close()
