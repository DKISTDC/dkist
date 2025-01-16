---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.11.5
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Visualizing DKIST Data

In this session we will look at how to take a better look at the actual data once we've downloaded it.
As usual, first we'll need a dataset.
We'll use the VISP data we downloaded at the end of the last notebook.

```{code-cell} python
---
tags: [skip-execution]
---
%matplotlib tk
```

```{code-cell} python
import dkist
import matplotlib.pyplot as plt

ds = dkist.load_dataset('~/sunpy/data/BKPLX')
ds
```

## Plotting our data

Getting started with plotting a dataset is straightforward.
`Dataset` provides a `plot()` method which makes a decent default plot of the data.

```{code-cell} python
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

```{code-cell} ipython
ds
```

So the list needed to specify the default ordering would be `[None, None, 'y', 'x']`.
If instead we want to plot the image formed by the raster scan at a particular wavelength and Stokes value, we can change which axes we specify as the x and y axes of the plot.
For this example we will slice the data down to a particular region of interest.

```{code-cell} python
small_ds = ds[0, 150:300, :, 1010:-1010]
```

Note that since this removes the first axis, the `plot_axes` argument is now only three items long.

```{code-cell} ipython
# Plot 'raster scan step number' on the y axis and 'spatial along slit' on the x axis
small_ds.plot(plot_axes=['y', None, 'x'])
plt.show()
```

You may have noticed this plot took somewhat longer to draw than the previous one.
This is for the same reason as we discussed when talking about reducing the size of dataset downloads: when you slice across the array in a different direction to how it's stored in the files, you have to reference multiple files to create the slice.
So while the first plot only had to load values from one file at a time, the one above needs to get one line of the array from each of 150 files in order to draw the slice.
If you try to animate it, it then needs to do this again at every step.

```{warning}
For the above example we have very deliberately sliced the data to a size that is manageably small.
Due to some known issues in the plotting code, plotting slices across the data in this way is extremely slow and is not really viable for a full-size dataset.
See issue [#256](https://github.com/DKISTDC/dkist/issues/256) for more details.
```

You can also use `plot_axes` to create a line plot, by specifying only one axis of the data.
So to plot a spectrum at a fixed Stokes, time and raster location we can tell `plot` to use the dispersion axis as the x axis.

```{code-cell} ipython
ds.plot(plot_axes=[None, None, 'x', None])
plt.show()
```

It is also possible to slice the data manually and just plot the result.
This of course creates a new dataset so it will only plot the axes that remain, without sliders or the ability to step through the values of the other axes.

```{code-cell} ipython
# Plot the same data as above
ds[0, 0, :, 0].plot()
plt.show()
```

### Using AIA as a Context Image

#### Fetching an AIA Image
Next we are going to use the coordinate information in the VISP dataset to plot VISP's field of view over an AIA image.
To do this we are going to use {obj}`sunpy.map`.

```{code-cell} python
import sunpy.map
from sunpy.net import Fido, attrs as a
import astropy.units as u
```

First we shall search for an AIA image closest to the start time of the VISP dataset.

```{code-cell} python
start_time = ds.inventory["startTime"]
end_time = ds.inventory["endTime"]
```

```{code-cell} python
res = Fido.search(a.Time(start_time, end_time, start_time), a.Instrument.aia, a.Wavelength(19.3 * u.nm)) # change this to 160?
res
```

```{code-cell} python
aia_files = Fido.fetch(res)
aia_files
```

Now we have an AIA image file, let's read it with `sunpy`.

```{code-cell} python
import sunpy.map
```

```{code-cell} python
aia = sunpy.map.Map(aia_files)
aia
```

Now let's make a simple plot of the AIA map.
The sunpy map object has a `.plot()` method which sets up a lot of stuff for us, but we will manually make the figure and axes.

```{code-cell} python
fig = plt.figure()
ax = plt.subplot(projection=aia)
aia.plot(axes=ax)
```

#### Computing the VISP field of View

As we can see from the docstring of `aia.draw_quadrangle` we can specify a bottom left and a top right coordinate.
Remember we can calculate the world coordinates of a dataset like this:


```python
coords = ds.wcs.array_index_to_world(0, 0, 0, 0)
coords
```

This gives us the full coordinates at one corner of the dataset.
Of course, the spectral, time and Stokes coordinates are of no use to us here so we can access the longitude and latitude by indexing to get just the `SkyCoord`:


```{code-cell} python
coords[1]
```


```python
ds
```

At this point we _can_ simply call `array_index_to_world()` again for the other side of the array to get the opposite corner and pass both in to `draw_quadrangle()`. However, instead we'll demonstrate a useful feature of `SkyCoord`

As we briefly saw previously, a `SkyCoord` object can be an array.
Therefore if we pass `array_index_to_world` an array-like input it will give us an array-like output:


```python
corners = ds.wcs.array_index_to_world([0, 0],
                                      [0, ds.data.shape[1]-1],
                                      [0, 0],
                                      [0, ds.data.shape[3]-1])
corners
```


```python
# Text below is wrong but hopefully this whole example will change anyway.
```

So here for the first array index dimension we are giving it the bottom left row index and the top right row index and for the second array index dimension we are giving it the bottom left column index and the top right column index.

This gives us back a `SkyCoord` with two elements in both `Tx` and `Ty`:


```python
corners[1].Tx
```

#### Plotting VISP Field of View on AIA Images

Now we can use this to overplot the field of view of the VISP image:


```{code-cell} python
fig = plt.figure()
ax = plt.subplot(projection=aia)
aia.plot(axes=ax)
aia.draw_quadrangle(corners[1])
```

Finally, we can zoom in a little.
If you are doing this interactively you can zoom in with the UI, here I shall do it by specifying pixel coordinates:

```{code-cell} python
_ = ax.axis((1200, 2400, 1600, 2800))
fig
```
