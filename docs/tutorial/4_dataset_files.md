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

(dkist:tutorial:dataset-exploring-files)=
# Exploring Files in a `Dataset`

In this chapter you will learn:

- How to access dataset metadata from the FITS headers
- How `Dataset` tracks FITS files and what to expect when slicing the data
- How to obtain the quality report and preview movie for a dataset.

First we need to re-create our dataset object from the last chapter.

```{code-cell} ipython3
---
tags: [keep-inputs]
editable: true
slideshow:
  slide_type: ''
---
import astropy.units as u
from astropy.visualization import quantity_support
import numpy as np

import dkist
from dkist.data.sample import VISP_L1_KMUPT
```

```{code-cell} ipython3
:tags: [keep-inputs]

ds = dkist.load_dataset(VISP_L1_KMUPT)
ds
```

The `Dataset` object allows us to do some basic inspection of the dataset as a whole without having to download the entire thing, using the metadata in the FITS headers.
This will save you a good amount of time and also ease the load on the DKIST servers.
For example, we can check the seeing conditions during the observation and discount any data which will not be of high enough quality to be useful.
We will go through this as an exercise in a later tutorial.

+++

## The `headers` table

The FITS headers from every file in a dataset are duplicated and stored in the ASDF file.
This means that all the metadata about each file is accessible using only the ASDF file before downloading any of the actual data.
(It also means any changes you make to the headers in the headers table won't be reflected in the FITS files.)
These headers are stored as a table in the `headers` attribute of the `Dataset`.

```{code-cell} ipython3
:tags: [output_scroll]

ds.headers
```

Since the headers are stored as a table, it is straightforward to inspect a keyword for all files at once.
For example, to see the time of every frame in the dataset:

```{code-cell} ipython3
:tags: [output_scroll]

ds.headers['DATE-AVG']
```

Alternatively if we want to look at all the columns but fewer files, we can either slice the table directly:

```{code-cell} ipython3
ds.headers[:5]
```

or we can slice the dataset to give us the files we want to inspect:

```{code-cell} ipython3
ds[:, 0].headers
```

The table is an instance of {obj}`astropy.table.Table`, and can therefore be inspected and manipulated in any of the usual ways for Table objects.
Details of how to work with `Table` can be found in the astropy documentation: {ref}`astropy-table`.
Notably though, columns can be used as arrays in many contexts.
They can therefore be used for plotting, which allows us to visually inspect how metadata values vary over the many files in the dataset.
For example, we might want to inspect the seeing conditions and plot the Fried parameter for all frames.

First, if you're not familiar with all of the keywords in the header, they can be checked in the documentation ({ref}`level-one-data-products`).
Helpfully, `Dataset` provides some additional metadata which includes a link to the specific version of that documentation used when making these FITS files:

```{code-cell} ipython3
ds.meta['inventory']['headerDocumentationUrl']
```

If you follow this link and then click on "Level One FITS Specification" you will find a list of all the FITS keywords used for level 1 data with a description of each.
Using this we can find that the Fried parameter is stored with the keyword `"ATMOS_R0"`.
Then it's trivial to plot this information:

```{code-cell} ipython3
import matplotlib.pyplot as plt

plt.plot(ds[0].headers['ATMOS_R0'])
plt.show()
```

Or we can use multiple columns from the headers to compare information or look at related values.

```{code-cell} ipython3
ds.headers.keys()
```

```{code-cell} ipython3
fig, ax = plt.subplots()
times = ds[0].axis_world_coords("time")[0]
time_delta = (times - times[0]).to_value(u.s)

with quantity_support():
    sc = ax.scatter(ds[0].headers["TAZIMUTH"] * u.deg, ds[0].headers["ELEV_ANG"] * u.deg, c=time_delta)
ax.set_ylabel("Elevation")
ax.set_xlabel("Azimuth")
fig.colorbar(sc, label="Time delta from start of scan [s]")
```

## Downloading the quality report and preview movie

For each dataset a quality report is produced during calibration which gives useful information about the quality of the data.
This is accessible through the `Dataset`'s `quality_report()` method, which will download a PDF of the quality report to the base path of the dataset.
This uses parfive underneath, which is the same library `Fido` uses, so it will return the same kind of `results` object.
If the download has been successful, this can be treated as a list of filenames.

```{code-cell} ipython3
qr = ds.files.quality_report()
qr
```

This method takes the optional arguments `path` and `overwrite`.
`path` allows you to specify a different location for the download, and `overwrite` is a boolean which tells the method whether or not to download a new copy if the file already exists.

Similarly, each dataset also has a short preview movie showing the data.
This can be downloaded in exactly the same way as the quality report but using the `preview_movie()` method:

```{code-cell} ipython3
pm = ds.files.preview_movie()
pm
```

We can also embed the hosted version of the preview movie in our notebook:

```{code-cell} ipython3
---
tags: [keep-inputs]
---
from IPython.display import VimeoVideo

# We need the ID of the video, which is the path component
vimeo_id = ds.inventory["browseMovieUrl"].split("/")[-1]
VimeoVideo(vimeo_id, width=600, height=450)
```

## Tracking files

`Dataset` tracks information about the individual files that make up the dataset in the `files` attribute.

```{code-cell} ipython3
ds.files
```

This tells us that our (4, 425, 980, 2554) data array is stored as 1700 files, each containing an array of (1, 980, 2554).
The list of filenames referenced by this dataset can also be accessed with:

```{code-cell} ipython3
ds.files.filenames
```

`Dataset` also knows the base path of the data - the path where the data is (or will be) saved.

```{code-cell} ipython3
ds.files.basepath
```

When we download the data for this dataset later on, this is where it will be saved.
This defaults to the location of the ASDF file.
Remember that there may be thousands of FITS files in a dataset, so in general you may want to use the path interpolation feature of the various download functions to keep your them arranged sensibly.
This is why we have been downloading ASDF files to their own folders.

We have mentioned already that slicing a dataset down to only the portion of it that interests us can be a way of reducing the size of the download once we want to actually get the data. We'll come back to both file tracking and downloads, but for now let us look at how our slicing operations impact the number of files.

```{code-cell} ipython3
ds.data.shape
```

```{code-cell} ipython3
ds.files
```

Here we can see that our initial starting point with the full dataset is an array of (4, 425, 980, 2554) datapoints stored in 1700 FITS files. Notice that the array in each file is of size (1, 980, 2554) - the dimensions match the spatial and dispersion axes of the data (with a dummy axis). Each file therefore effectively contains a single 2D image taken at a single raster location and polarization state, and many of these files put together make the full 4D dataset.

Next let us slice our dataset as we did in the last chapter, and this time look at how that impacts the tracked files.

```{code-cell} ipython3
stokes_i = ds[0]
stokes_i.data.shape
```

```{code-cell} ipython3
stokes_i.files
```

Since this slice only contains Stokes I, it only needs the files containing the corresponding data; those measured at the other polarization states have been dropped, leaving 425.

```{code-cell} ipython3
scan = ds[0, :, 200]
scan.data.shape
```

```{code-cell} ipython3
scan.files
```

In this case, however, although the dataset is obviously smaller it still spans the same 425 files. This is because we haven't sliced by raster location and are therefore taking one row of pixels from every file. To reduce the number of files any further we must look at fewer raster step positions:

```{code-cell} ipython3
feature = ds[0, 100:200, :, 638:-628]
feature.data.shape
```

```{code-cell} ipython3
feature.files
```

It is therefore important to pay attention to how your data are stored across files. As noted before, slicing sensibly can significantly reduce how many files you need to download, but it can also be a relevant concern when doing some computational tasks and when plotting, as every file touched by the data will need to be opened and loaded into memory.
