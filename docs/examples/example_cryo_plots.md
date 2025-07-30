---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.6
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

(dkist:examples:cryo-plots)=
# Visualizing Cryo-NIRSP Data


```{code-cell} ipython3
import dkist
import numpy as np
import astropy.units as u
import matplotlib.pyplot as plt
from astropy.coordinates import SpectralCoord

from dkist.data.sample import CRYO_L1_TJKGC, CRYO_L1_MSCGD
```


```{code-cell} ipython3
sp = dkist.load_dataset(CRYO_L1_TJKGC)
ci = dkist.load_dataset(CRYO_L1_MSCGD)
```

```{code-cell} ipython3
sp_sum_wave = sp.rebin((-1,-1,1), function=np.sum).squeeze()
sp_wave_mean = sp.rebin((1,1,-1), function=np.mean).squeeze()

sp_subtracted = sp - (sp_wave_mean.data * sp_wave_mean.unit)[..., None]

peak_idx = sp_sum_wave.wcs.world_to_array_index(SpectralCoord(1079.75, unit=u.nm))

sp_subtracted_peak = sp_subtracted[:,:,int(peak_idx)]
```

Calculate pixel size
First get a 2x2 pixel grid
```{code-cell} ipython3
space_2 = sp[:2,:2,0].axis_world_coords()[0]
```

 We calculate pixel size by calculating the step in both lat and lon. (lon is backwards because bugs)
```{code-cell} ipython3
dlon = np.abs(space_2[1,1].Tx - space_2[0,0].Tx)
dlat = space_2[1,1].Ty - space_2[0,0].Ty

aspect = dlon / dlat
```

```{code-cell} ipython3
fig = plt.figure(figsize=(12,6), layout="constrained")

ax1 = fig.add_subplot(1, 2, 1, projection=sp_subtracted_peak)
ax1.set_title("Mean subtracted line peak")
sp_subtracted_peak.plot(axes=ax1, cmap="Greys_r")
ax1.set_aspect(aspect)

ax2 = fig.add_subplot(1, 2, 2, projection=sp_wave_mean)
ax2.set_title("Mean wavelength")
sp_wave_mean.plot(axes=ax2)
ax2.set_aspect(aspect)
plt.show()
```

## Plot Context Imager Data

```{code-cell} ipython3
slit_coords = sp[:100,:,0].axis_world_coords()[0][::10,:]

fig = plt.figure(layout="constrained")
vmin, vmax = np.nanpercentile(ci[0].data, [1,99])
ax = ci[0].plot(vmin=vmin, vmax=vmax)
lims = ax.axis()
for slit_pos in slit_coords:
    ax.plot_coord(slit_pos)
ax.axis(lims)
ax.coords.grid(color='white', alpha=0.6, linestyle='dotted',
               linewidth=0.5)
plt.show()
```
