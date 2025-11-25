import gzip
from pathlib import Path

import matplotlib as mpl
import numpy as np
from matplotlib.colors import ListedColormap

from dkist.data.test import rootdir

#from dkist.data.test import rootdir

__all__ = ["cmaps", "colormap_test_fits"]

zipfiles = rootdir.rglob("final_L1-*.fits.gz")

for zf in zipfiles:
    with gzip.open(zf, mode="rb") as gfo:
        with open(zf.parent / zf.name.replace(".gz", ""), mode="wb") as afo:
            afo.write(gfo.read())


def cmap_from_csv(fname):
    cmapvals = np.loadtxt(fname, skiprows=1, delimiter=",", comments=None, dtype=str)

    colourname = fname.name[5:].strip(".csv")
    return ListedColormap(cmapvals[:, 1], name=colourname)


cmap_files = list(Path(__file__).parent.glob("cmap-*.csv"))
cmaps = sorted([cmap_from_csv(f) for f in cmap_files], key=lambda m: m.name)

colormap_test_fits = {instrument: list((rootdir / instrument).glob("*/final_L1-*.fits")) for instrument in ["VISP", "VBI"]}

for cmap in cmaps:
    mpl.colormaps.register(cmap, name=cmap.name)
