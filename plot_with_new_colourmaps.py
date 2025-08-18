import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from dkist import load_dataset
from dkist.data.sample import VISP_L1_KMUPT, VBI_L1_NZJTB, CRYO_L1_TJKGC, CRYO_L1_MSCGD
from pathlib import Path
from astropy.coordinates import SpectralCoord
import astropy.units as u

def cmap_from_csv(fname):
    cmapvals = np.loadtxt(fname, skiprows=1, delimiter=',', comments=None, dtype=str)

    colourname = f.name[5:].strip('.csv')
    return ListedColormap(cmapvals[:, 1], name=colourname)

cmap_files = Path('.').glob('cmap-*.csv')

# for dsfile in [VBI_L1_NZJTB]:
#     ds = load_dataset(dsfile)
#     ds = ds.slice_tiles[0]
#     for tile in ds.flat:
#         tile.data = tile.data.compute()
#     instrument = ds.combined_headers[0]['INSTRUME']

#     fig = plt.figure(figsize=(24, 24))
#     for f in cmap_files:
#         cmap = cmap_from_csv(f)
#         print(f"Plotting {instrument} in {cmap.name}")

#         ds.plot(np.s_[:], aspect='auto', cmap=cmap)#, vmin=np.percentile(ds.data, 2), vmax=np.percentile(ds.data, 98))
#         plt.savefig(f'colormap-tests/{instrument}_{cmap.name}.png')
#     plt.close()

for dsfile in [VISP_L1_KMUPT, CRYO_L1_TJKGC]: #, CRYO_L1_MSCGD]:
# for dsfile in [CRYO_L1_TJKGC]:
    ds = load_dataset(dsfile)
    instrument = ds.headers[0]['INSTRUME']
    peak_idx = ds.rebin((-1, -1, 1), function=np.sum).squeeze().wcs.world_to_array_index(SpectralCoord(1079.75, unit=u.nm))
    datmean = ds.data.mean(axis=2)
    if instrument == 'VISP':
        # continue
        ds = ds[0, :, 0]
    else:
        continue
        ds = ds[:, :, peak_idx]
        ds.data = ds.data - datmean
    ds.data = ds.data.compute()

    fig = plt.figure(figsize=(24, 18))
    for f in cmap_files:
        cmap = cmap_from_csv(f)
        print(f"Plotting {instrument} in {cmap.name}")

        ds.plot(aspect='auto', cmap=cmap)#, vmin=np.percentile(ds.data, 2), vmax=np.percentile(ds.data, 98))
        plt.savefig(f'colormap-tests/{instrument}_{cmap.name}.png')
    plt.close()

