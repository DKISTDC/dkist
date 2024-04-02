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

(dkist:tutorial:more-dataset)=
# More `Dataset`

Firstly we need to re-create our dataset object from the last tutorial.

```{code-cell} ipython
from sunpy.net import Fido, attrs as a
import dkist
import dkist.net

res = Fido.search(a.dkist.Dataset('BKPLX'))
files = Fido.fetch(res, path="~/dkist_data/{dataset_id}")
ds = dkist.load_dataset(files)
```

The `Dataset` object allows us to do some basic inspection of the dataset as a whole without having to download the entire thing, using the metadata in the FITS headers.
This will save you a good amount of time and also ease the load on the DKIST servers.
For example, we can check the seeing conditions during the observation and discount any data which will not be of high enough quality to be useful.
We will go through this as an exercise in a later tutorial.

## The `headers` table

The FITS headers from every file in a dataset are duplicated and stored in the ASDF file.
This means that all the metadata about each file is accessible using only the ASDF file before downloading any of the actual data.
(It also means any changes you make to the headers in the headers table won't be reflected in the FITS files.)
These headers are stored as a table in the `headers` attribute of the `Dataset`.

```{code-cell} ipython
---
tags: [output_scroll]
---
ds.headers
```

Since the headers are stored as a table, it is straightforward to inspect a keyword for all files at once.
For example, to see the time of every frame in the dataset:

```{code-cell} ipython
---
tags: [output_scroll]
---
ds.headers['DATE-AVG']
```

Or we can look at one or more rows (i.e.: files) by slicing the table.

```{code-cell} ipython
ds.headers[:5]
```

The table is an instance of {obj}`astropy.table.Table`, and can therefore be inspected and manipulated in any of the usual ways for Table objects.
Details of how to work with `Table` can be found on the astropy documentation.
Notably though, columns can be used as arrays in many contexts.
They can therefore be used for plotting, which allows us to visually inspect how metadata values vary over the many files in the dataset.
For example, we might want to inspect the seeing conditions and plot the Fried parameter for all frames.

First, if you're not familiar with all of the keywords in the header, they can be checked in the documentation.
Helpfully, `Dataset` provides some additional metadata which includes a link to that documentation:

```{code-cell} ipython
ds.meta['inventory']['headerDocumentationUrl']
```

If you follow this link and then click on "Level One FITS Specification" you will find a list of all the FITS keywords used for level 1 data with a description of each.
Using this we can find that the Fried parameter is stored with the keyword `"ATMOS_R0"`.
Then it's trivial to plot this information:

```{code-cell} ipython
import matplotlib.pyplot as plt

plt.plot(ds.headers['ATMOS_R0'])
plt.show()
```

## Tracking files

`Dataset` tracks information about the individual files that make up the dataset in the `files` attribute.

```{code-cell} ipython
ds.files
```

This tells us that our (20, 4096, 4096) data array is stored as 20 files, each containing an array of (4096, 4096).
Since the filenames are automatically generated from observation metadata, the `files` attribute can also track those before we even download the data.

```{code-cell} ipython
ds.files.filenames
```

`Dataset` also knows the base path of the data - the path where the data is (or will be) saved.

```{code-cell} ipython
ds.files.basepath
```

When we download the data for this dataset later on, this is where it will be saved.
So in general you may want to use the path interpolation feature of the various download functions to keep your data files arranged sensibly, as we have for this example.

### Reducing file downloads
We have mentioned a few times already that we can reduce the size of a data download by finding just the data that interests us and slicing the dataset down to just that portion.
However, there is an important point to note about this, which is that you need to keep in mind how the data are stored across the dataset's files.

As we saw before, each FITS file contains effectively a 2D image - a single raster scan at one polarisation state - and we have many of these files to make a full 4D dataset.
What this means is that if we look at a subset of the scan steps or polarisation states, we will reduce the number of files across which the array is stored.

```{code-cell} ipython
ds[0]
```

First, notice that when we slice a `Dataset` like this, the output we get here shows us not just the updated array shape but also the updated dimensions.
Because we're looking at a single polarisation state, that axis and the corresponding physical axis have been removed.

Going back to the `files` attribute, we can see that we do indeed have fewer files for this subset of the data.

```{code-cell} ipython
ds[0].files
```

However, if we decide we want to look at a single wavelength, we are taking a row of pixels from every single file.
So although we reduce the dimensions of the array, we are not reducing the number of files we need to reference - and therefore download.

```{code-cell} ipython
ds[:, :, 500, :].data.shape
```
```{code-cell} ipython
ds[:, :, 500, :].files
```
## Downloading the quality report and preview movie

For each dataset a quality report is produced during calibration which gives useful information about the quality of the data.
This is accessible through the `Dataset`'s `quality_report()` method, which will download a PDF of the quality report to the base path of the dataset.
This uses parfive underneath, which is the same library `Fido` uses, so it will return the same kind of `results` object.
If the download has been successful, this can be treated as a list of filenames.

```{code-cell} ipython
qr = ds.files.quality_report()
qr
```

This method takes the optional arguments `path` and `overwrite`.
`path` allows you to specify a different location for the download, and `overwrite` is a boolean which tells the method whether or not to download a new copy if the file already exists.

Similarly, each dataset also has a short preview movie showing the data.
This can be downloaded in exactly the same way as the quality report but using the `preview_movie()` method:

```{code-cell} ipython
pm = ds.files.preview_movie()
pm
```
