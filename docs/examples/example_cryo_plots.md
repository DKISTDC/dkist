---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.17.2
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

First let's load the sample Cryo-NIRSP data.

```{code-cell} ipython3
sp = dkist.load_dataset(CRYO_L1_TJKGC) # Load the spectropolimeter (SP) sample dataset
ci = dkist.load_dataset(CRYO_L1_MSCGD) # Load the context imager (CI) sample dataset
```

Next we'll sum the SP data over the spatial dimensions to produce a spectral profile, which we can plot.

```{code-cell} ipython3
sp_sum_wave = sp.rebin((-1,-1,1), function=np.sum).squeeze()
```

```{code-cell} ipython3
fig = plt.figure()
sp_sum_wave.plot()
```

Now we will calculate the mean count value over all wavelengths for each spatial pixel and subtract that from the dataset.
To do this we have to subtract a {obj}`~astropy.units.Quantity` object with a dummy axis for wavelength.

```{code-cell} ipython3
sp_mean = sp.rebin((1,1,-1), function=np.mean).squeeze()
sp_subtracted = sp - (sp_mean.data * sp_mean.unit)[..., None]
```

We can then extract the array index of the peak spectral line and use that to select the scan at that wavelength position.

```{code-cell} ipython3
peak_idx = sp_sum_wave.wcs.world_to_array_index(SpectralCoord(1079.75, unit=u.nm))

sp_subtracted_peak = sp_subtracted[:,:,int(peak_idx)]
```

Next we will need to calculate the pixel size in both Longitude and Latitude, which we will use to ensure we can plot the data with the proper aspect ratio.
First get a 2x2 grid of SkyCoord objects:

```{code-cell} ipython3
space_2 = sp[:2,:2,0].axis_world_coords()[0] # [0] because we only care about space, not time
```

 We calculate pixel size by calculating the step in both lat and lon.

```{code-cell} ipython3
dlon = np.abs(space_2[1,1].Tx - space_2[0,0].Tx)
dlat = np.abs(space_2[1,1].Ty - space_2[0,0].Ty)

aspect = dlon / dlat
```

Finally, we can plot both our mean-subtracted scan at the peak wavelength and the mean values over all all wavelengths.

```{code-cell} ipython3
fig = plt.figure(figsize=(7, 5), layout="constrained")

ax1 = fig.add_subplot(2, 1, 1, projection=sp_subtracted_peak)
ax1.set_title("Mean subtracted line peak")
sp_subtracted_peak.plot(axes=ax1, cmap="Greys_r", aspect=aspect)

ax2 = fig.add_subplot(2, 1, 2, projection=sp_mean)
ax2.set_title("Mean counts")
sp_mean.plot(axes=ax2, aspect=aspect)
plt.show()
```

## Plot Context Imager Data

Using the CI data we can now also plot the slit positions on the context image.

```{code-cell} ipython3
# We will just plot every tenth slit position from the first hundred
slit_coords = sp[:100,:,0].axis_world_coords()[0][::10,:]

fig = plt.figure(layout="constrained")
vmin, vmax = np.nanpercentile(ci[0].data, [1,99])
ax = ci[0].plot(vmin=vmin, vmax=vmax)
# Slit is longer than CI so get the axis limits before plotting the slit
lims = ax.axis()
for slit_pos in slit_coords:
    ax.plot_coord(slit_pos)
# Crop back to CI
ax.axis(lims)
# Overlay coordinates grid
ax.coords.grid(color='white', alpha=0.6, linestyle='dotted',
               linewidth=0.5)
plt.show()
```
