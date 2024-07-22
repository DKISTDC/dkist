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

(dkist:tutorial:visp-dataset)=
# Working with a VISP `Dataset`

In this tutorial you will learn how to open a dataset and inspect it, then choose a subset of the data to download.

A `Dataset` class is constructed from the ASDF file for that dataset, this ASDF file contains the following information:
* A table containing all the headers from all FITS files that comprise the dataset.
* A copy of the Data Center's inventory record for the dataset.
* A `gwcs` object which provides coordinate information for the whole dataset.
* A list of all the component FITS files and the required order to combine them into a single array.

In this tutorial we will create `Dataset`s using only the ASDF files.
This will mean we won't have access to the data arrays in the FITS files, but everything else will function the same.

## Constructing `Dataset` Objects

We can construct a `Dataset` by providing a path to an ASDF file.
Here we shall first fetch an ASDF file with Fido and then pass it to `dkist.load_dataset`:

```{code-cell} ipython3
:tags: [keep-inputs]

from astropy.time import Time

import dkist
import dkist.net
from sunpy.net import Fido, attrs as a
```

```{code-cell} ipython3
res = Fido.search(a.dkist.Dataset('BKPLX'))
files = Fido.fetch(res, path="~/dkist_data/{instrument}_{dataset_id}")
files
```

Remember that the file we have downloaded is a single ASDF file, **not** the whole dataset.
We can use this file to construct the `Dataset`:

```{code-cell} ipython3
ds = dkist.load_dataset(files)
```

Now we have a `Dataset` object which describes the shape, size and physical dimensions of the array, but doesn't yet contain any of the actual data.
This may sound unhelpful but we'll see how it can be very powerful.

Let's have a look at the basic representation of the `Dataset`.

```{code-cell} ipython3
ds
```

This gives us a lot of information about the both the *pixel dimensions* of the data (the coordinates of the detector grid) and the *world dimensions* (the physical coordinates of the image).
Before we go on to using the `Dataset` for inspecting the data, we will take a moment to discuss coordinate systems and consider what the `Dataset` output above means.

## `Dataset` and `NDCube`: Coordinate aware arrays

The `Dataset` class is an extension to [SunPy's `NDCube` class](https://docs.sunpy.org/projects/ndcube/).
Much of the following functionality is available in all `NDCube` objects.
See the `NDCube` documentation for more detail.

### Pixel, Array and World Ordering

We will use the following definitions to distinguish between pixel, array, and world coordinates:

* **Pixel** ordering is defined as "Cartesian" ordering, or the same as Fortran ordering or column major. This is the ordering used by FITS files and WCS objects in Python.
* **Array** ordering is defined a C or row-major ordering. This is use by Python's numpy arrays, as Python is implemented in C.
* **World** coordinates are the physical coordinates that correspond to pixel coordinates. These are not always in either pixel or array order, but tend to be close to pixel order.

The pixel grid will always be aligned with the array, so pixel and array coordinates are the same except for the ordering.

### Coordinates, Arrays, Pixels, oh my!

A key aspect of the `Dataset` is that it is coordinate aware.
That is, it is able to map between array indices and physical dimensions.
This means that you can easily convert from a position in the array to a location defined by physical coordinates.

To achieve this, `Dataset` tracks the pixel and world coordinates independently in the `wcs` (World Coordinate System) attribute.
The output above tells us that we have a 4-dimensional pixel grid and a 5-dimensional world grid:

```{code-cell} ipython3
ds.wcs.pixel_n_dim, ds.wcs.world_n_dim
```

The next few lines tell us about the data array and the pixel dimensions.

```{code-cell} ipython3
ds.data
```

This tells us that the data are (or will be) stored in a dask array, and the array dimensions.
(More on Dask and dask arrays in a later tutorial.)

We can get the corresponding **pixel** axis names with:

```{code-cell} ipython3
ds.wcs.pixel_axis_names
```

Note that these are in reverse order compared to the `ds` output earlier.
This is because they are in *pixel* order rather than *array* order.

Next we see the description of the world coordinates.
This information is also accessible through the `wcs` attribute:

```{code-cell} ipython3
ds.wcs.world_axis_names
```

This tells us the names of the physical axes, each of which corresponds to a type of phyical observation (lon/lat, time, wavelength, etc.) and has its own units.

```{code-cell} ipython3
ds.wcs.world_axis_physical_types, ds.wcs.world_axis_units
```

You will have noticed that the pixel and world coordinates have different numbers of dimensions.
This is because in this dataset the detector is not aligned with the solar latitude/longitude coordinate system, so any change in position along the detector slit will be equivalent to a change in both latitude and longitude.
To see this, we can look at the physical coordinates which correspond to each array axis, just as we did for the world axes.

```{code-cell} ipython3
ds.array_axis_physical_types
```

The final piece of output is the axis correlation matrix which summarises which pixel and world axes correspond to each other:

```{code-cell} ipython3
ds.wcs.axis_correlation_matrix
```

We can use all of this information about the dataset coordinates to convert from pixel to world coordinates or vice versa.
So if for example we want to plot our data at, say, a particular wavelength, we can find the corresponding array index with `ds.wcs.world_to_array_index()`
<!-- Actually put a calculation here when the function works -->

### Slicing Datasets

A useful feature of the `Dataset` class, which it inherits from `NDCube` is the ability to "slice" the dataset and get a smaller dataset, with the array and coordinate information in tact.

For example, to extract the Stokes I component of the dataset we would do:

```{code-cell} ipython3
ds[0]
```

this is because the stokes axis is the first array axis, and the "I" profile is the first one (0 indexing).

Note how we have dropped a world coordinate, this information is preserved in the `.global_coords` attribute, which contains the coordinate information which applies to the whole dataset:

```{code-cell} ipython3
ds[0].global_coords
```

We can also slice the data further, as we would for a normal numpy array.
So for instance we can select a small section of the image in Stokes I at some arbitrary wavelength:

```{code-cell} ipython3
cropped = ds[0, 200:300, 100, 950:1600]
cropped
```

Notice again that this has reduced the dimensionality of the world coordinates as well as of the data itself.
