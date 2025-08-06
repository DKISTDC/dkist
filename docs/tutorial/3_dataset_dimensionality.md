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

(dkist:tutorial:dataset-dimensionality)=
# Dimensionality of a `Dataset`

In this chapter you will learn how to open a dataset and inspect it, then choose a subset of the data to download.

As previously discussed we know that a "DKIST dataset" is comprised of multiple files, including an ASDF and many FITS files.
The Python tools represent all these files with the {obj}`dkist.Dataset` class.

A `Dataset` object is constructed from the ASDF file for that dataset.
This ASDF file contains the following information:
* A table containing all the headers from all FITS files that comprise the dataset.
* A copy of the Data Center's inventory record for the dataset.
* A `gwcs` object which provides coordinate information for the whole dataset.
* A list of all the component FITS files and the required order to combine them into a single array.

In this chapter we will create `Dataset`s using only the ASDF files.
This will mean we won't have access to the data arrays in the FITS files, but everything else will function the same.

```{note}
The `Dataset` object is the default structure for DKIST datasets.
However, data from VBI and DL-NIRSP are presented to the user as multiple `Dataset` objects representing mosaic tiles.
To handle these data, the we use the `TiledDataset` object instead.
For more detail on `TiledDataset`, see {ref}`dkist:tutorial:tiled-dataset`.
```

## DKIST Sample data

In this chapter and the next few, we will use some sample datasets which are provided with the `dkist` package.
These sample datasets provide convenient examples to work with and contain some FITS files which do not require Globus to access.
They can be imported from `dkist.data.sample` and for this chapter we will use the VISP one:

```{code-cell} ipython3
from dkist.data.sample import VISP_L1_KMUPT

VISP_L1_KMUPT
```

This constant defines the path to a folder containing the metadata ASDF and a few data files for a small VISP dataset.
These are automatically downloaded the first time you import the sample data so that the dataset is always available.

+++

## Constructing `Dataset` Objects

The Python tools provide a utility function {obj}`dkist.load_dataset` which loads an ASDF file and creates one or more {obj}`dkist.Dataset` or {obj}`dkist.TiledDataset` objects.
This function takes one of several different kinds of input:

- a string representation of either; a valid ASDF file or a directory containing one;
- a `pathlib.Path` object representing a valid ASDF or directory containing one;
- a `parfive.results.Results` object as returned by `sunpy.Fido.fetch` (this will only work if _all_ results in the table are valid DKIST ASDF files); or
- a list or tuple of any combination of the above.

+++

## Loading a VISP Dataset

For the rest of this tutorial we are going to be using sample data provided with the `dkist` package.
These sample datasets provide convenient examples to work with and contain some FITS files which do not require Globus to access.

The sample datasets can be imported from `dkist.data.sample`, here we use a VISP one:

```{code-cell} ipython3
import dkist

ds = dkist.load_dataset(VISP_L1_KMUPT)
```

Now we have a {obj}`dkist.Dataset` object which describes the shape, size and physical dimensions of the array, but doesn't assume the presence of any of the actual data.
This may sound unhelpful but we'll see how it can be very powerful.

First let's have a look at the basic representation of the `Dataset`.

```{code-cell} ipython3
ds
```

This tells us that we have a 4-dimensional data cube and what values the axes correspond to.
Importantly, it not only gives us information about the *pixel* axes (the actual dimensions of the array itself), but also the *world* axes (the physical quantities related to the observation).
It also gives us a correlation matrix showing how the pixel axes relate to the world axes.

+++

## `Dataset` and `NDCube`: Coordinate aware arrays

The `Dataset` class is an extension to [SunPy's `NDCube` class](https://docs.sunpy.org/projects/ndcube/).
In this section we shall demonstrate some of the key functionality of `NDCube` with DKIST data.

### Pixel, Array and World Ordering

Before we jump into using the `Dataset` class we need to clarify some definitions:

* **Pixel** ordering is defined as "Cartesian" ordering, or the same as Fortran ordering or column major. This is the ordering used by FITS files and WCS objects in Python.
* **Array** ordering is defined as C or row-major ordering. This is used by Python's numpy arrays, as Python is implemented in C.
* **World** coordinates are the physical coordinates that correspond to pixel coordinates. These are not always in either pixel or array order, but tend to be close to pixel order.

The pixel grid will always be aligned with the array, so pixel and array coordinates are the same except for the ordering.

### Coordinates, Arrays, Pixels, oh my!

A key aspect of the `Dataset` is that it is coordinate aware.
That is, it is able to map between array indices and physical dimensions.
This means that you can easily convert from a position in the array to a location defined by physical coordinates.

The first thing we can inspect about our dataset is the dimensionality of the underlying array.

```{code-cell} ipython3
ds.shape
```

These are the **array** dimensions.
We can get the corresponding **pixel** axis names with:

```{code-cell} ipython3
ds.wcs.pixel_axis_names
```

note how these are reversed from one another, we can print them together with:

```{code-cell} ipython3
for name, length in zip(ds.wcs.pixel_axis_names[::-1], ds.shape):
    print(f"{name}: {length}")
```

These axes map onto world axes via the axis correlation matrix as we saw above:

```{code-cell} ipython3
ds
```

We can get a list of the world axes which correspond to each array axis with:

```{code-cell} ipython3
ds.array_axis_physical_types
```

This property is a list with one element for every array axis containing a tuple of the world axis physical types of each world axis correlated with that array axis.
So the first array axis has one physical type `'phys.polarization.stokes'` but the second has three (lat, lon and time).

Using the WCS object, we can convert between pixel or array coordinates and world coordinates:

```{code-cell} ipython3
# Convert array indices to world (physical) coordinates
ds.wcs.array_index_to_world(0, 10, 20, 30)
```

```{code-cell} ipython3
# Convert pixel coords to world coords
world = ds.wcs.pixel_to_world(30, 20, 10, 0)
world
```

and we can also do the reverse:

```{code-cell} ipython3
ds.wcs.world_to_pixel(*world)
```

```{code-cell} ipython3
ds.wcs.world_to_array_index(*world)
```

Finally, it's possible to get the coordinates corresponding to each world axis using {obj}`~dkist.Dataset.axis_world_coords`.

```{code-cell} ipython3
:tags: [output_scroll]

ds.axis_world_coords()
```

This method (when called without any arguments) returns a tuple of coordinate objects covering all the different world axes, in this case it returns a `SkyCoord` for the two spatial axes, a `SpectralCoord` for the spectral axis, a `Time` object for the temporal axis and a `StokesCoord` for the Stokes axis.

+++

It's possible to pass an argument to `axis_world_coords` which is one or more world axis physical types (or unique substrings thereof) so this would just return the coordinates along the temporal world axis

```{code-cell} ipython3
:tags: [output_scroll]

ds.axis_world_coords('time')
```

### Slicing Datasets

Another useful feature of the `Dataset` class, which it inherits from `NDCube`, is the ability to "slice" the dataset and return a smaller dataset, with the array and coordinate information in tact.
The syntax for this is exactly as you would expect for a NumPy array, but it is worth taking quick look at how the coordinates are handled.

For example, to extract the Stokes I component of the dataset we would access the first item of the first axis:

```{code-cell} ipython3
stokes_i = ds[0]
stokes_i
```

And to get a full raster scan in Stokes I at a single wavelength we would further index the dispersion axis:

```{code-cell} ipython3
scan = ds[0, :, 200]
scan
```

First, notice that when we slice a Dataset like this, the output we get here shows us not just the updated array shape but also the updated dimensions. Because we're looking at a single polarisation state and a single wavelength, those axes and the corresponding world axes have been removed. This gives us a new dataset with the smaller 425x2554 pixel dimensions and the world axes associated with those. The relationship between the remaining pixel and world axes stays the same as shown in the correlation matrix.

You may notice that we have "lost" some information here. Having dropped two world axes we no longer have the coordinate information for them, and so cannot tell what world coordinates the new dataset corresponds to. However, this information is preserved in the dataset, just not in the axes. There is a `.global_coords` attribute, which contains coordinate information applicable to the whole dataset. In this case that would be the wavelength and the Stokes parameter:

```{code-cell} ipython3
scan.global_coords
```

Again following usual NumPy slicing syntax, we can also slice out a section of an axis of the dataset:

```{code-cell} ipython3
# Select a hundred raster steps and the central half of the slit in Stokes I
feature = ds[0, 100:200, :, 638:-638]
feature
```

Notice again that this has reduced the dimensionality of the world coordinates as well as of the data itself.
