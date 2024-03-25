---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.1
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

(dkist:tutorial:visualizing)=
# Visualizing DKIST Data

In this session we will look at how to take a better look at the actual data once we've downloaded it.
As usual, first we'll need a dataset.
We'll use the VISP data we downloaded at the end of the last tutorial.

```{code-cell} ipython3
import dkist
import matplotlib.pyplot as plt

from sunpy.net import Fido, attrs as a
import dkist.net
```

```{code-cell} ipython3
res = Fido.search(a.dkist.Dataset("BKPLX"))
asdf_file = Fido.fetch(res, path="~/dkist_data/{dataset_id}")

ds = dkist.load_dataset(asdf_file)
```

## Plotting our data

Getting started with plotting a dataset is straightforward.
`Dataset` provides a `plot()` method which makes a decent default plot of the data.

```{code-cell} ipython3
ds.plot()
plt.show()
```

Since our dataset is 4D and most users will only have access to a 2D screen, a slice has to be taken through the data.
That slice is defined by how the data are ordered and stored in the FITS files.
In this case, since the FITS files are arrays of the spatial axis vs wavelength, this is the slice that has been plotted for a single polarisation state and scan step.

This is where the sliders at the bottom of the plot come in.
These correspond to the axes of the data that aren't shown, and allow you to step through those axes.
This allows you to set the polarisation state and scan step for which the slice is taken, and show the data slice at those coordinates.
Alternatively, you can click the play button at the side of each slider to animate the plot and loop through all those values.

Of course, you will probably find you don't always want to slice through the data in the default way.
In this case, you can use the `plot_axes` argument to `plot()`.
This takes a list which defines which axes to plot as the slice and which to use as the sliders.
The list should contain `"x"` and `"y"` in the locations corresponding to the axes we want to plot, and `None` elsewhere.
The ordering for this is the same as for the pixel dimensions as shown in the `Dataset` summary.

```{code-cell} ipython3
ds
```

So the list needed to specify the default ordering would be `[None, None, 'y', 'x']`.
If instead we want to plot the image formed by the raster scan at a particular wavelength and Stokes value, we would do this:

+++

```{warning}
Plotting a raster scan of VISP data is currently very slow due to known performance issues in how varying pointing over the raster is handled. See issue [#256](https://github.com/DKISTDC/dkist/issues/256) for more details.
```

```{code-cell} ipython3
ds.plot(plot_axes=[None, 'y', None, 'x'])
plt.show()
```

You may have noticed this plot took somewhat longer to draw than the previous one.
This is for the same reason as we discussed when talking about reducing the size of dataset downloads: when you slice across the array in a different direction to how it's stored in the files, you have to reference multiple files to create the slice.
So while the first plot only had to load values from one file at a time, the one above needs to get one line of the array from each of 1000 files in order to draw the slice.
If you try to animate it, it then needs to do this again at every step.

You can also use `plot_axes` to create a line plot, by specifying only one axis of the data.
So to plot a spectrum at a fixed Stokes, time and raster location we can tell plot to use the dispersion axis as the x axis.

```{code-cell} ipython3
ds.plot(plot_axes=[None, None, 'x', None])
plt.show()
```

It is also possible to slice the data manually and just plot the result.
This of course creates a new dataset so it will only plot the axes that remain, without sliders or the ability to step through the values of the other axes.

```{code-cell} ipython3
:tags: [skip-execution]

ds[0, :, 400, :].plot()
plt.show()
```

## More advanced plotting

For the next few examples we'll go back to using some VBI data.

```{code-cell} ipython3
res = Fido.search(a.dkist.Dataset("AJQWW"))
asdf_file = Fido.fetch(res, path="~/dkist_data/{dataset_id}")

# We extract the top left tile of the VBI mosaic
ds = dkist.load_dataset(asdf_file)[0, 0]
```

Now let's take a slice of the data and plot it.
This returns an axes object which we haven't needed before, but this time we'll assign it to a variable so that we can manipulate the plot.
This allows us to do a number of things with it, such as show the grid of the plot.

```{code-cell} ipython3
ax = ds[0].plot()
ax.grid(True)
```

What you will probably notice here is that the grid is not aligned with the pixel grid of the image.
This is because the plot returns a `WCSAxesSubplot`, which is coordinate-aware and automatically uses the world coordinate system for the grid.
It also supports all the usual ways of manipulating subplots.

Since the `WCSAxesSubplot` is coordinate-aware, we can also use it for plotting coordinates directly, without having to do any manual conversions.
To do this, we can use the `.plot_coord()` method.

```{code-cell} ipython3
import astropy.units as u
from astropy.coordinates import SkyCoord

coord = SkyCoord(-181*u.arcsec, 112*u.arcsec, frame='helioprojective', observer='earth', obstime=ds.headers['DATE-AVG'][0])

ax = ds[0].plot()
ax.grid(True)
# Plot the coordinate as a white circle
ax.plot_coord(coord, 'wo')
plt.show()
```
