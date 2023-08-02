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
# Searching for DKIST Datasets

In this tutorial you will search for DKIST datasets available at the DKIST Data Center.

Each dataset comprises a number of different files:
  * An ASDF file containing all the metadata, and no data.
  * A quality report PDF.
  * An mp4 preview movie.
  * A (large) number of FITS files, each containing a "calibrated exposure".
  
The ASDF, quality report and preview movie can all be downloaded without authenticating, the FITS files require the use of Globus, which is covered in [this tutorial](./5_downloading_data.html).

## Using `Fido.search`

The search interface used for searching the dataset holding at the DKIST data center is {obj}`sunpy.net.Fido`.
With `Fido` you can search for datasets and download their corresponding ASDF files.
To register the DKIST search with `Fido` we must also import `dkist.net`.

```{code-cell} python
import dkist.net
import astropy.units as u
from sunpy.net import Fido, attrs as a
```

`Fido` searches are built up from "attrs", which we imported above as `a`.
These attrs are combined together with either logical and or logical or operations to make complex queries.
Let's start simple and search for all the DKIST datasets which are not embargoed:

```{code-cell} python
Fido.search(a.dkist.Embargoed(False))
```

Because we only specified one attr, and it was unique to the dkist client (it started with `a.dkist`) only the DKIST client was used.

If we only want VBI datasets, that are unembargoed, between a specific time range we can use multiple attrs:

```{code-cell} python
Fido.search(a.Time("2022-06-02 17:00:00", "2022-06-02 18:00:00") & a.Instrument.vbi & a.dkist.Embargoed(False))
```

Note how the `a.Time` and `a.Instrument` attrs are not prefixed with `dkist`.
These are general attrs which can be used to search multiple clients.

So far the returned results have had to match all the attrs provided, because we have used the `&` (logical and) operator to join them.
If we want results that match either one of multiple options we can use the `|` operator.

```{code-cell} python
res = Fido.search((a.Instrument.vbi | a.Instrument.visp) & a.dkist.Embargoed(False))
res
```

As you can see this has returned two separate tables, one for VBI and one for VISP.

## Working with Results Tables

In this case, although we've searched for VISP data as well, let's first look at just the VBI results, the first table.
```{code-cell} python
vbi = res[0]
vbi
```

We can do some sorting and filtering using this table.
For instance, if we are interested in choosing data with a particular $r_0$ value, we can show only that column plus a few to help us identify the data:
```{code-cell} python
vbi["Dataset ID", "Start Time", "Average Fried Parameter", "Embargoed"]
```

or sort based on the $r_0$ column, and pick the top 5 rows:
```{code-cell} python
vbi.sort("Average Fried Parameter")
vbi[:5]
```

Once we have selected the rows we are interested in we can move onto downloading the ASDF files.

## Downloading Files with `Fido.fetch`

```{note}
Only the ASDF files can be downloaded with `Fido`.
To download the FITS files containing the data, see the [downloading data tutorial](../5_downloading_data.html)
```

To download files with `Fido` we pass the search results to `Fido.fetch`.

If we want to download the first VBI file we searched for earlier we can do so like this:
```{code-cell} python
Fido.fetch(vbi[0])
```
This will download the ASDF file to the sunpy default data directory `~/sunpy/data`, we can customise this with the `path=` keyword argument.

A simple example of specifying the path is:

```{code-cell} python
---
tags: [skip-execution]
---
Fido.fetch(vbi[0], path="data/my_vbi_data/")
```

This will download the ASDF file as `data/my_vbi_data/<filename>.asdf`.

With the nature of DKIST data being a large number of files, FITS + ASDF for a whole dataset, we probably want to keep each dataset in its own folder.
`Fido` makes this easy by allowing you to provide a path template rather than a specific path.
To see the list of parameters we can use in these path templates we can run:
```{code-cell} python
vbi.path_format_keys()
```

So if we want to put each of our ASDF files in a directory named with the Dataset ID and Instrument we can do:

```{code-cell} python
Fido.fetch(vbi[:5], path="~/sunpy/data/{instrument}/{dataset_id}/")
```
