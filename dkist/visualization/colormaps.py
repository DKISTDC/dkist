from pathlib import Path

import matplotlib as mpl

#from dkist.data.test import rootdir

__all__ = ["cmaps", "colormap_test_fits"]

rootdir = Path("~").expanduser() / "oss-projects" / "dkist" / "dkist" / "data" / "test"

def cmap_from_csv(fname):
    cmapvals = np.loadtxt(fname, skiprows=1, delimiter=",", comments=None, dtype=str)

    colourname = fname.name[5:].strip(".csv")
    return ListedColormap(cmapvals[:, 1], name=colourname)


cmap_files = list(Path().glob("cmap-*.csv"))
cmaps = sorted([cmap_from_csv(f) for f in cmap_files], key=lambda m: m.name)

colormap_test_fits = {instrument: list((rootdir / instrument).glob("*/final_L1-*.fits")) for instrument in ["VISP", "VBI"]}

for cmap in cmaps:
    mpl.colormaps.register(cmap, name=cmap.name)
