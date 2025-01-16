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

As previously discussed we know that a "DKIST dataset" is comprised of many files, including an ASDF and many FITS files.
The user tools represent all these files with the {obj}`dkist.Dataset` class.

A `Dataset` object is constructed from the ASDF file for that dataset.
This ASDF file contains the following information:
* A table containing all the headers from all FITS files that comprise the dataset.
* A copy of the Data Center's inventory record for the dataset.
* A `gwcs` object which provides coordinate information for the whole dataset.
* A list of all the component FITS files and the required order to combine them into a single array.

In this tutorial we will create `Dataset`s using only the ASDF files.
This will mean we won't have access to the data arrays in the FITS files, but everything else will function the same.

## Constructing `Dataset` Objects

The Python tools provide a utility function `dkist.load_dataset()` which loads an ASDF file and creates one or more `Dataset` objects. This function takes one of several different kinds of input:

- a string representation of either a valid ASDF file or a directory containing one;
- a `pathlib.Path` object representing a valid ASDF or directory containing one;
- a `parfive.results.Results` object as returned by `sunpy.Fido.fetch` (this will only work if _all_ results in the table are valid DKIST ASDF files); or
- a list or tuple of any combination of the above.

Here we shall first fetch an ASDF file with Fido and then pass it to `dkist.load_dataset()`:

```{code-cell} ipython
---
tags: [keep-inputs]
---
import dkist
import dkist.net
from sunpy.net import Fido, attrs as a
from astropy.time import Time
```

```{code-cell} ipython
# Search with Fido for a suitable dataset
res = Fido.search(a.dkist.Dataset('BKPLX'))

res
```
```{code-cell} ipython
files = Fido.fetch(res, path="~/sunpy/data/{instrument}/{dataset_id}")
files
```

Remember that the file we have downloaded is a single ASDF file, **not** the whole dataset.
We can use this file to construct the `Dataset`:

```{code-cell} ipython
ds = dkist.load_dataset(files[0])
```

Now we have a `Dataset` object which describes the shape, size and physical dimensions of the array, but doesn't yet contain any of the actual data.
This may sound unhelpful but we'll see how it can be very powerful.

First let's have a look at the basic representation of the `Dataset`.

```{code-cell} ipython
ds
```

This tells us that we have a 4-dimensional data cube and what values the axes correspond to.
Importantly, it not only gives us information about the *pixel* axes (the actual dimensions of the array itself), but also the *world* axes (the physical quantities related to the observation).
It also gives us a correlation matrix showing how the pixel axes relate to the world axes.

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
```{code-cell} python
ds.dimensions
```

These are the **array** dimensions.
We can get the corresponding **pixel** axis names with:

```{code-cell} python
ds.wcs.pixel_axis_names
```

note how these are reversed from one another, we can print them together with:
```{code-cell} python
for name, length in zip(ds.wcs.pixel_axis_names[::-1], ds.dimensions):
    print(f"{name}: {length}")
```

These axes map onto world axes via the axis correlation matrix we saw above:
```{code-cell} python
dkist.dataset.utils.pp_matrix(ds.wcs)
```

We can get a list of the world axes which correspond to each array axis with:
```{code-cell} python
ds.array_axis_physical_types
```

Finally, we can convert between pixel or array coordinates and world coordinates:

```{code-cell} ipython
# Convert array indices to world (physical) coordinates
ds.wcs.array_index_to_world(0, 10, 20, 30)
```

```{code-cell} ipython
# Convert pixel coords to world coords
world = ds.wcs.pixel_to_world(30, 20, 10, 0)
world
```

and we can also do the reverse:

```{code-cell} python
ds.wcs.world_to_pixel(*world)
```

```{code-cell} python
ds.wcs.world_to_array_index(*world)
```

This tells us the names of the physical axes, each of which corresponds to a type of phyical observation (lon/lat, time, wavelength, etc.) and has its own units.
Finally, it's possible to get all the axis coordinates along one or more axes:

```{warning}
This might eat all your <del>cat</del> RAM.

The algorithm used to calculate these coordinates in ndcube isn't as memory efficient as it could be, and when working with the large multi-dimensional DKIST data you can really notice it!
```

You will have noticed that the pixel and world coordinates have different numbers of dimensions.
This is because in this dataset the detector is not aligned with the solar latitude/longitude coordinate system, so any change in position along the detector slit will be equivalent to a change in both latitude and longitude.
To see this, we can look at the physical coordinates which correspond to each array axis, just as we did for the world axes.
```{code-cell} python
---
tags: [output_scroll]
---
ds.axis_world_coords()
```

```{code-cell} python
---
tags: [output_scroll]
---
ds.axis_world_coords('time')
```

### Slicing Datasets

Another useful feature of the `Dataset` class, which it inherits from `NDCube` is the ability to "slice" the dataset and get a smaller dataset, with the array and coordinate information in tact.
The syntax for this is exactly as you would expect for a NumPy array, but it is worth taking quick look at how the coordinates are handled.

For example, to extract the Stokes I component of the dataset we would access the first item of the first axis:

```{code-cell} python
stokes_i = ds[0]
stokes_i
```

And to get a full raster scan in Stokes I at a single wavelength we would further index the dispersion axis:


```{code-cell} python
scan = ds[0, :, 200]
scan
```

First, notice that when we slice a Dataset like this, the output we get here shows us not just the updated array shape but also the updated dimensions. Because we're looking at a single polarisation state and a single wavelength, those axes and the corresponding world axes have been removed. This gives us a new dataset with the smaller 425x2554 pixel dimensions and the world axes associated with those. The relationship between the remaining pixel and world axes stays the same as shown in the correlation matrix.

You may notice that we have "lost" some information here. Having dropped two world axes we no longer have the coordinate information for them, and so cannot tell what world coordinates the new dataset corresponds to. However, this information is preserved in the dataset, just not in the axes. There is a `.global_coords` attribute, which contains coordinate information applicable to the whole dataset. In this case that would be the wavelength and the Stokes parameter:


```python
scan.global_coords
```

Again following usual NumPy slicing syntax, we can also slice out a section of an axis of the dataset:

```python
# Select a hundred raster steps and the central half of the slit in Stokes I
feature = ds[0, 100:200, :, 638:-638]
feature
```

### Slicing and files

We have mentioned already that slicing a dataset down to only the portion of it that interests us can be a way of reducing the size of the download once we want to actually get the data. We'll come back to both file tracking and downloads, but for now let us look at how our slicing operations impact the number of files.

```{code-cell} python
ds.data.shape, ds.files
```

Here we can see that our initial starting point with the full dataset was an array of (4, 425, 980, 2554) datapoints stored in 1700 FITS files. Notice that the array in each file is of size (1, 980, 2554) - the dimensions match the spatial and dispersion axes of the data (with a dummy axis). Each file therefore effectively contains a single 2D image taken at a single raster location and polarization state, and many of these files put together make the full 4D dataset.

Next let us look at our sliced datasets.

```python
stokes_i.data.shape, stokes_i.files
```

Now since the dataset only contains Stokes I, we only need the files containing the corresponding data and those measured at the other polarization states have been dropped, leaving 425.


```python
scan.data.shape, scan.files
```

In this case, however, although the dataset is obviously smaller it still spans the same 425 files. This is because we haven't sliced by raster location and are therefore taking one row of pixels from every file. To reduce the number of files any further we must look at fewer wavelengths:


```python
feature.data.shape, feature.files
```

Notice again that this has reduced the dimensionality of the world coordinates as well as of the data itself.
It is therefore important to pay attention to how your data are stored across files. As noted before, slicing sensibly can significantly reduce how many files you need to download, but it can also be a relevant concern when doing some computational tasks and when plotting, as every file touched by the data will need to be opened and stored in memory.
