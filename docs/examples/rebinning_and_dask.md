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

# Rebinning and How to Use Dask

## Fundamentals of Dask

In this session we are going to use the example of rebinning VISP data to discuss how the Dask array backing the `Dataset` object works.
Dask is a Python package for out-of-memory and parallel computation in Python, it provides an array-like object where data is only loaded and processed on demand.
`Dataset` uses Dask to track the data arrays, which it stores in the `Dataset.data` attribute.

To demonstrate this let's load our VISP dataset from yesterday, and slice it to a more manageable size again.

```{code-cell} python
import dkist
import dkist.net
import matplotlib.pyplot as plt

ds = dkist.Dataset.from_directory('~/sunpy/data/VISP/AGLKO/')
ds = ds[0, 520:720, :, 1000:1500]
```

This Dask object behaves in many ways just like a numpy array.
For instance, it can indexed and sliced in the same way.

```{code-cell} python
ds.data[:, :, :200]
```

And it has many of the same methods for calculating useful properties of the data, such as `min()`, `max()`, `sum()`, etc.
These are in fact just wrappers around the numpy functions themselves, so they behave in the same way.
For example, to find the sum over the spatial dimensions of our cropped data to make a spectrum, we could do:

```{code-cell} python
ds.data.sum(axis=(0,2))
```

What you will notice when you call these functions that they don't return a number as you would expect.
Instead they give us a Dask array which represents the result of that calculation.
This is because Dask delays the actual calculation of the value until you explicitly tell it to do it using the `compute()` method.

```{code-cell} python
spectrum = ds.data.sum(axis=(0,2)).compute()
plt.plot(spectrum)
```

A benefit of this is that since the operations returns us another Dask array, we can do more calculations with that, and those are also delayed.
This means that you can string together any number of calculations and only perform the costly step of getting the actual answer once.
So if we want to find the location of the lowest value in this spectrum, we can do

```{code-cell} python
spectrum = ds.data.sum(axis=(0, 2))
wl_idx = spectrum.argmin()
wl_idx = wl_idx.compute()
wl = ds.wcs.pixel_to_world(0, wl_idx, 0)[1]
wl
```

When performing these operations, Dask breaks up the array into chunks, and operations will generally be faster and use less memory when they require fewer chunks.
In the case of a `Dataset`, these chunks are aligned with the files, so each chunk essentially consists of the array stored in one FITS file.
In the future we may break down a FITS file into more chunks, so the whole array does not always have to be read.

## Rebinning with `NDCube`

```{code-cell} python
---
tags: [keep-inputs]
---
import dkist
import matplotlib.pyplot as plt

ds = dkist.Dataset.from_directory("~/sunpy/data/VISP/AGLKO")
ds
```

We are going to use the {obj}`ndcube.NDCube.rebin` method:
```{code-cell} python
---
tags: [output_scroll]
---
help(ds.rebin)
```

This rebin method, can reduce the resolution of a dataset, *by integer numbers of pixels*.

So if we wanted to combine 7 pixels along the slit dimension together we can do this:
```{code-cell} python
ds.rebin((1, 1, 1, 7))
```

```{note}
Because we are using Dask, this hasn't actually done any computation yet, but is has reduced the size of the dask array.
```

Let's compare two spectra, one from the rebinned dataset and one from the original:
```{code-cell} python
ds_I = ds[0]
ds_I_rebinned = ds[0].rebin((1, 1, 7))
```

```{code-cell} python
plt.figure()
ax = ds_I[500, :, 1000].plot()
ds_I_rebinned[500, :, int(1000/7)].plot(axes=ax, linestyle="--")
```

As one final example of rebin, let's rebin in both the rastering dimension and the slit.
Let's rebin to bins of 10x10 pixels, to do this we will need to make the slit axis divisible by 10, so we crop it down by 5 pixels.

```{code-cell} python
ds_r10 = ds[0, ..., :-5].rebin((10, 1, 10))
```
```{code-cell} python
plt.figure()
ax = ds_I[500, :, 1000].plot()
ds_I_rebinned[500, :, int(1000/7)].plot(axes=ax, linestyle="--")
ds_r10[50, :, 100].plot(axes=ax, linestyle="..")
```

## Rebinning in Parallel

By default dask will parallelise operations as much as is possible, over the available cores in your machine.
The Dask project also supports parallelising over the distributed compute such as HPC or cloud computing.
For this next section we are going to use this `distributed` package as a way of visualising the parallelisation.

If you want to follow along with this bit you will need to install these packages, if you want to just watch that's also fine.
```{code-cell} shell
---
tags: [skip-execution]
---
conda install distributed bokeh
```

```{code-cell} python
from dask.distributed import Client
client = Client()
client
```
```{code-cell} python
rebinned_ds = ds[0, ..., :-5].rebin((10, 1, 10))
```

```{code-cell} python
---
tags: [skip-execution]
---
computed_data = rebinned_ds.data.compute()
```

```{code-cell} python
---
tags: [skip-execution]
---
rebinned_ds._data = computed_data  # This is naughty
```

```{code-cell} python
---
tags: [skip-execution]
---
rebinned_ds.plot()
```
