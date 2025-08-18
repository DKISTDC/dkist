---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.17.2
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

(dkist:tutorial:search-and-download)=
# Searching for DKIST Datasets

In this chapter we will cover how to search for DKIST datasets available at the DKIST Data Center.

In DKIST data parlance, a "dataset" is the smallest unit of data that is searchable from the data centre, and represents a single observation from a single instrument at a single pass band.
Each dataset comprises a number of different files:
  * An ASDF file containing all the metadata, and no data.
  * A quality report PDF.
  * An mp4 preview movie.
  * A (large) number of FITS files, each containing a "calibrated exposure".

All of these files, apart from the FITS files containing the data, can be downloaded irrespective of embargo status.

For each of these "datasets" the DKIST Data Center keeps a "dataset inventory record" which is a limited set of metadata about the dataset on which you can search, either through the web portal or the `dkist` Python package.
The ASDF, quality report and preview movie can all be downloaded without authentication, the FITS files require the use of Globus.


## Using `Fido.search`

The search interface we are going to use is {obj}`sunpy.net.Fido`.
`Fido` supports many different sources of data, some built into `sunpy` like the VSO and some in plugins like `dkist` or `sunpy-soar`.
With `Fido` you can search for DKIST datasets and download their corresponding ASDF files.
To register the DKIST search with `Fido` we must also import `dkist.net`.

```{code-cell} ipython3
import numpy as np
import astropy.units as u
from sunpy.net import Fido, attrs as a
import dkist.net
```

`Fido` searches are built up from attributes, referred to in python as `attrs`, which we have imported above as `a`.
These attrs are combined together with either logical AND or logical OR operations to make complex queries.
Let's start simple and search for all the DKIST datasets which are not embargoed:

```{code-cell} ipython3
:tags: [output_scroll]

Fido.search(a.dkist.Embargoed(False))
```

Because we only specified one attr, and it was unique to the dkist client (it started with `a.dkist`) only the DKIST client was used.

If we only want VBI datasets, that are unembargoed, between a specific time range we can use multiple attrs:

```{code-cell} ipython3
Fido.search(a.Time("2022-06-02 17:00:00", "2022-06-02 18:00:00") & a.Instrument.vbi & a.dkist.Embargoed(False))
```

Note how the `a.Time` and `a.Instrument` attrs are not prefixed with `dkist` - these are general attrs which can be used to search multiple sources of data.

So far all returned results have had to match all the attrs provided, because we have used the `&` (logical AND) operator to join them.
If we want results that match either one of multiple options we can use the `|` operator.

```{code-cell} ipython3
:tags: [output_scroll]

Fido.search((a.Instrument.vbi | a.Instrument.visp) & a.dkist.Embargoed(False))
```

As you can see this has returned two separate tables, one for VBI and one for VISP.

Because `Fido` can search other clients in addition to the DKIST specific client, you can create more complex queries. For example, a search for VISP data and context images from AIA at the same time:

```{code-cell} ipython3
time = a.Time("2022-06-02 17:00:00", "2022-06-02 18:00:00")
aia = a.Instrument.aia & a.Wavelength(17.1 * u.nm) & a.Sample(30 * u.min)
visp = a.Instrument.visp & a.dkist.Embargoed(False)

Fido.search(time, aia | visp)
```

Here we have used a couple of different attrs.
`a.Sample` limits the results to one per time window given, and `a.Wavelength` searches for specific wavelengths of data.
Also, we passed our attrs as positional arguments to `Fido.search`.
This is a little bit of sugar to prevent having to specify a lot of brackets; all arguments have the and (`&`) operator applied to them.

## Working with Results Tables

A Fido search returns a {obj}`sunpy.net.fido_factory.UnifiedResponse` object, which contains all the search results from all the different clients and requests made to the servers.

```{code-cell} ipython3
res = Fido.search((a.Instrument.vbi | a.Instrument.visp) & a.dkist.Embargoed(False))
type(res)
```

The `UnifiedResponse` object provides a couple of different ways to select the results you are interested in.
It's possible to select just the results returned by a specific client by name, in this case all the results are from the DKIST client so this changes nothing.

```{code-cell} ipython3
:tags: [output_scroll]

res["dkist"]
```

This object is similar to a list of tables, where each response can also be selected by the first index:

```{code-cell} ipython3
:tags: [output_scroll]

vbi = res[0]
vbi
```

Now we have selected a single set of results from the `UnifiedResponse` object, we can see that we have a `DKISTQueryResponseTable` object:

```{code-cell} ipython3
type(vbi)
```

This is a subclass of {obj}`astropy.table.QTable`, which means we can do operations such as sorting and filtering with this table.

We can display only some columns:

```{code-cell} ipython3
:tags: [output_scroll]

vbi["Dataset ID", "Start Time", "Average Fried Parameter", "Embargoed"]
```

Sort based on Fried Parameter

```{code-cell} ipython3
# Sort affects the table in-place
vbi.sort("Average Fried Parameter", reverse=True)
```

```{code-cell} ipython3
vbi["Product ID", "Average Fried Parameter"]
```

We can also use table operations to filter to results with good average seeing, but not unphysically high.

```{code-cell} ipython3
fried_parameter = vbi["Average Fried Parameter"]
good_seeing = vbi[np.logical_and(fried_parameter > 0.2, fried_parameter < 1)]
good_seeing[:5]["Product ID", "Average Fried Parameter"]
```

Once we have selected the rows we are interested in we can move onto downloading the ASDF files.

## Downloading Files with `Fido.fetch`

```{note}
Only the ASDF files can be downloaded with `Fido`.
To download the FITS files containing the data, see the [downloading data tutorial](dkist:tutorial:downloading-data)
```

To download files with `Fido` we pass the search results to `Fido.fetch`.

If we want to download the first VBI dataset we searched for earlier, we can do so like this:

```{code-cell} ipython3
Fido.fetch(vbi[0])
```

```{note}
When downloading ASDF files with Fido, if the file already exists then the download will usually be skipped, to save unnecessary load.
However, occasionally the ASDF files will be updated at the Data Center.
Fido is able to check for this, and if the files are different, the newer one will be downloaded.
It is therefore encouraged to keep the Fido download in your scripts even after downloading the ASDF file, as this will keep your metadata up to date.
```

This will download the ASDF file to the sunpy default data directory `~/sunpy/data`, we can customise this with the `path=` keyword argument.

A simple example of specifying the path is:

```{code-cell} ipython3
:tags: [skip-execution]

Fido.fetch(vbi[0], path="data/mypath")
```

This will download the ASDF file as `data/mypath/filename.asdf`.

With the nature of DKIST data being a large number of files - FITS + ASDF for a whole dataset - we probably want to keep each dataset in it's own folder.
`Fido` makes this easy by allowing you to provide a path template rather than a specific path.
To see the list of parameters we can use in these path templates we can use a helper method on the `DKISTQueryResponseTable`:

```{code-cell} ipython3
vbi.path_format_keys()
```

So if we want to put each of our ASDF files in a directory named with the Dataset ID and Instrument we can do:

```{code-cell} ipython3
Fido.fetch(vbi[:5], path="~/sunpy/data/{instrument}/{dataset_id}/")
```

Storing each dataset in its own folder may seem unnecessary right now, since we are only downloading a single ASDF file for each one. However, this extra level of sorting will become useful later on when we start to download the FITS files.
