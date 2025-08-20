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

In this example we will talk about visualising both spectrograph and context imager datasets.

```{code-cell} ipython3
import numpy as np
import astropy.units as u
import matplotlib.pyplot as plt
from astropy.coordinates import SpectralCoord
from matplotlib.collections import LineCollection
from matplotlib.colors import PowerNorm

import dkist
from dkist.data.sample import CRYO_L1_TJKGC, CRYO_L1_MSCGD
```

First let's load the sample Cryo-NIRSP data.

```{code-cell} ipython3
sp = dkist.load_dataset(CRYO_L1_TJKGC) # Load the spectropolimeter (SP) sample dataset
ci = dkist.load_dataset(CRYO_L1_MSCGD) # Load the context imager (CI) sample dataset
```

The first thing we want to plot is a line profile for the whole dataset.
To do this we use the {obj}`dkist.Dataset.rebin` method to sum all the spatial pixels, to give us a summary profile for the whole dataset.

```{code-cell} ipython3
sp_sum_wave = sp.rebin((-1,-1,1), function=np.sum).squeeze()
sp_sum_wave
```

```{code-cell} ipython3
fig = plt.figure()
sp_sum_wave.plot()
```

Now we will calculate the mean count value over all wavelengths for each spatial pixel and subtract that from the dataset.
To do this we have to subtract a {obj}`~astropy.units.Quantity` object with a dummy axis for wavelength.

```{code-cell} ipython3
sp_mean = sp.rebin((1,1,-1), function=np.mean).squeeze()
```

```{code-cell} ipython3
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
dlon = np.abs(space_2[1,0].Tx - space_2[0,0].Tx)
dlat = np.abs(space_2[0,1].Ty - space_2[0,0].Ty)

aspect = dlon / dlat
```

Finally, we can plot both our mean-subtracted scan at the peak wavelength and the mean values over all all wavelengths.

```{code-cell} ipython3
fig = plt.figure(figsize=(7, 5), layout="constrained")

ax1 = fig.add_subplot(2, 1, 1, projection=sp_subtracted_peak)
ax1.set_title("Mean subtracted line peak")
sp_subtracted_peak.plot(axes=ax1, cmap="Greys_r", aspect=aspect)

# Define keyword arguments in a dict so we can reuse them
# Note we use the "contours" type due to the nature of the WCS
grid_kwargs = {"grid_type": "contours", "linestyle": "dotted", "alpha": 0.6, "linewidth": 0.5}
# Draw gridlines for HPC.
ax1.coords[0].grid(color="w", **grid_kwargs)
ax1.coords[1].grid(color="w", **grid_kwargs)

ax2 = fig.add_subplot(2, 1, 2, projection=sp_mean)
ax2.set_title("Mean counts")
sp_mean.plot(axes=ax2, aspect=aspect)
# Draw gridlines for HPC.
ax2.coords[0].grid(color="k", **grid_kwargs)
ax2.coords[1].grid(color="k", **grid_kwargs)
plt.show()
```

## Plot Context Imager Data

Cryo-NIRSP has both a slit-spectrograph and a context imager, which follows the position of the slit.

The sample data we are using in this example only has the first context imager file downloaded, so here we plot the first context imager image.

+++

```{note}
There's a known issue with the Cryo-NIRSP context imager currently where the WCS is incorrect for the ordering of the first spatial array dimension. To address this issue we will flip the data along this axis.
```

```{code-cell} ipython3
# Correct ordering issue to make coordinates correct.
ci.data = ci.data[:, ::-1, :]
```

```{code-cell} ipython3
fig = plt.figure(layout="constrained")

# This data has many outliers, so we are going to clip it and scale it with a power law scaling
vmin, vmax = np.nanpercentile(ci[0].data, [1,99])
norm = PowerNorm(0.3, vmin=vmin, vmax=vmax)
ax = ci[0].plot(norm=norm)

# Overlay coordinates grid
ax.coords.grid(color='white', alpha=0.6, linestyle='dotted',
               linewidth=0.5)

plt.colorbar(label=f"{ci[0].unit:latex}")
plt.show()
```

Now we can plot the slit position. We do this by taking the first raster step position of the SP dataset and computing the world coordinates of each pixel along the slit.

```{code-cell} ipython3
slit_coords = sp[0,:,0].axis_world_coords()[0]  # Again, [0] extracts the spatial coordinates and drops time.

fig = plt.figure(layout="constrained")
# Reuse the norm from the first plot
ax = ci[0].plot(norm=norm)

ax.plot_coord(slit_coords, color="green")

# Overlay coordinates grid
ax.coords.grid(color='white', alpha=0.6, linestyle='dotted',
               linewidth=0.5)
plt.show()
```

Notice how the slit has a larger field of view along the latitude dimension. We can re-plot the image, and crop the extent of the plot back to the extent of the context imager.

```{code-cell} ipython3
slit_coords = sp[0,:,0].axis_world_coords()[0]  # Again, [0] extracts the spatial coordinates and drops time.

fig = plt.figure(layout="constrained")
# Reuse the norm from the first plot
ax = ci[0].plot(norm=norm)

# Slit is longer than CI so get the axis limits before plotting the slit
lims = ax.axis()

ax.plot_coord(slit_coords, color="green")

# Crop back to CI
ax.axis(lims)

# Overlay coordinates grid
ax.coords.grid(color='white', alpha=0.6, linestyle='dotted',
               linewidth=0.5)
plt.show()
```

Although we don't have all the context imager data in the sample dataset, we can overplot the slit position as it rasters across the image.
We set up multiple lines (plotted in pixel positions) and setup their colors to be mapped to the time delta from the first slit.

```{code-cell} ipython3
# Extract the first 100 slit positions
slit_coords, times = sp[:100, :, 0].axis_world_coords()
# Convert every 10th slit position to CI pixels
slit_pixels = ci[0].wcs.world_to_pixel(slit_coords[::10])
# Extract every 10th time
times = times[::10]
# Calculate the time delta from the first slit time.
deltas = (times - times[0]).to_value(u.s)
```

```{code-cell} ipython3
fig = plt.figure(layout="constrained")
# Reuse the norm from the first plot
ax = ci[0].plot(norm=norm)

# Construct a (n_slits, n_pixel, 2) array of slit coordinates
pix = np.array([slit_pixels[0].T, slit_pixels[1].T]).T
lines = LineCollection(pix, array=deltas, cmap="Greys")
ax.add_collection(lines)

# Overlay coordinates grid
ax.coords.grid(color='white', alpha=0.6, linestyle='dotted',
               linewidth=0.5)

fig.colorbar(lines, label="Slit position at time delta from image [s]")

ax.set_title(f"Cryo-NIRSP Context Imager at {ci[0].global_coords['time'].iso}")
plt.show()
```
