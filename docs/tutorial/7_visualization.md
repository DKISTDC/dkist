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

(dkist:tutorial:visualizing-data)=
# Visualizing DKIST Data

In this chapter we will cover plotting and visualization of both VISP and VBI data.
As usual, first we'll need a dataset.
Initially, we'll use the VISP sample data, but you can also use the data downloaded at the end of the last chapter.

```{code-cell} ipython3
:tags: [skip-execution]

%matplotlib widget
```

Then, as usual, first we'll need a dataset.

```{code-cell} ipython3
---
tags: [keep-inputs]
---
import matplotlib.pyplot as plt

import dkist
from dkist.data.sample import VISP_L1_KMUPT
```

```{code-cell} ipython3
ds = dkist.load_dataset(VISP_L1_KMUPT)
ds
```

+++

## Plotting our data

Getting started with plotting a dataset is straightforward.
`Dataset` provides a `plot()` method which makes a decent default plot of the data.

```{code-cell} ipython3
fig = plt.figure()
ds.plot(fig=fig)
```

+++

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

+++

So the list needed to specify the default ordering would be `[None, None, 'y', 'x']`.
If instead we want to plot the image formed by the raster scan at a particular wavelength and Stokes value, we can change which axes we specify as the x and y axes of the plot.
For this example we will slice the data down to a particular region of interest.

```{code-cell} ipython3
small_ds = ds[0, 150:300, :, 1010:-1010]
```

+++

Note that since this removes the first axis, the `plot_axes` argument is now only three items long.

```{code-cell} ipython3
fig = plt.figure()
# Plot 'raster scan step number' on the y axis and 'spatial along slit' on the x axis
small_ds.plot(fig=fig, plot_axes=['y', None, 'x'])
```

+++

You may have noticed this plot took longer to draw than the previous one.
This is for the same reason as we discussed when talking about reducing the size of dataset downloads: when you slice across the array in a different direction to how it's stored in the files, you have to reference multiple files to create the slice.
So while the first plot only had to load values from one file at a time, the one above needs to get one line of the array from each of 150 files in order to draw the slice.
If you try to animate it, it then needs to do this again at every step.

```{warning}
For the above example we have deliberately sliced the data to make it a more manageable size.
Due to some known issues in the plotting code, plotting slices across the data in this way is still slower than we'd like.
Full-sized datasets should therefore be plotted with caution.
See issue [#256](https://github.com/DKISTDC/dkist/issues/256) for more details.
```

You can also use `plot_axes` to create a line plot, by specifying only one axis of the data.
So to plot a spectrum at a fixed Stokes, time and raster location we can tell `plot` to use the dispersion axis as the x axis.

```{code-cell} ipython3
fig = plt.figure()
ds.plot(fig=fig, plot_axes=[None, None, 'x', None])
```

+++

It is also possible to slice the data manually and just plot the result.
This of course creates a new dataset so it will only plot the axes that remain, without sliders or the ability to step through the values of the other axes.

```{code-cell} ipython3
# Plot the same data as above
fig = plt.figure()
ax = ds[0, 0, :, 0].plot()
plt.show()
```

+++

## Plotting with `TiledDataset`

First, let us load the VBI sample data:

```{code-cell} ipython3
import dkist
from dkist.data.sample import VBI_L1_NZJTB

tds = dkist.load_dataset(VBI_L1_NZJTB)
```

+++

Again like {obj}`~dkist.Dataset`, {obj}`~dkist.TiledDataset` provides a plotting helper method.
This works slightly differently to `Dataset.plot()` though, in that it is not straightforward to animate a collection of tiles, which leaves the problem of how to display 3D data as a static image.
`TiledDataset.plot()` therefore takes an argument which specifies a slice to be taken through each tile, which must reduce it to a plottable two dimensions.

In the case of VBI, this argument will be a single number which specifies the index on the time axis to plot.

```{code-cell} ipython3
fig = plt.figure()
fig = tds.plot(0, figure=fig)
```

+++

As more DKIST instruments become available you may encounter tiled data with even more dimensions. In this case the slice argument would be either a tuple of integers or a numpy slice object. In either case it would be the indices required to reduce a tile to a 2D image.

You may notice in the plots above that the colour scale is independent for each tile. This is the default behaviour as it will allow features in each tile to be seen without being washed out by features in other tiles. However, for a more unified look you can tell `.plot()` to use the same scale for all tiles, with the `share_zscale` argument.

```{code-cell} ipython3
fig = plt.figure()
fig = tds.plot(0, share_zscale=True, figure=fig)
```
