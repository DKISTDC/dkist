import gzip
from pathlib import Path
import pytest

from dkist import load_dataset
from dkist.data.test import rootdir


def load_asdf(vispdir):
    ds = load_dataset(vispdir / "test_visp.asdf")


@pytest.mark.benchmark
def test_load_asdf(benchmark, tmp_path_factory):
    vispdir = tmp_path_factory.mktemp("data")
    with gzip.open(Path(rootdir) / "large_visp.asdf.gz", mode="rb") as gfo:
        with open(vispdir / "test_visp.asdf", mode="wb") as afo:
            afo.write(gfo.read())
    benchmark(load_asdf, vispdir)
