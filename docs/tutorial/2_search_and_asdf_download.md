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
(dkist:tutorial:search-and-download)=
# Searching for DKIST Datasets

In this tutorial you will search for DKIST datasets available at the DKIST Data Center.

Each dataset comprises a number of different files:
  * An ASDF file containing all the metadata, and no data.
  * A quality report PDF.
  * An mp4 preview movie.
  * A (large) number of FITS files, each containing a "calibrated exposure".
  
The ASDF, quality report and preview movie can all be downloaded without authenticating, the FITS files require the use of Globus, which is covered in {ref}`dkist:tutorial:downloading-data`.

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
Fido.search(a.Time("2023/10/16 18:45", "2023/10/16 18:48") & a.Instrument.vbi & a.dkist.Embargoed(False))
```

Note how the `a.Time` and `a.Instrument` attrs are not prefixed with `dkist`.
These are general attrs which can be used to search multiple clients.

So far the returned results have had to match all the attrs provided, because we have used the `&` (logical and) operator to join them.
If we want results that match either one of multiple options we can use the `|` operator.
Let's also restrict our search to a particular proposal, `pid_2_114`.

```{code-cell} python
res = Fido.search((a.Instrument.vbi | a.Instrument.visp) & a.dkist.Embargoed(False) & a.dkist.Proposal("pid_2_114"))
res
```

As you can see this has returned two separate tables, one for VBI and one for VISP, even though in fact the VBI table is empty.

## Working with Results Tables

In this case, since there is no VBI data, let's first look at just the VISP results, the second table.
```{code-cell} python
visp = res[1]
visp
```

We can do some sorting and filtering using this table.
For instance, if we are interested in choosing data with a particular $r_0$ value, we can show only that column plus a few to help us identify the data:
```{code-cell} python
visp["Dataset ID", "Start Time", "Average Fried Parameter", "Embargoed"]
```

or sort based on the $r_0$ column, and pick the top 3 results, showing the same columns as before:
```{code-cell} python
visp.sort("Average Fried Parameter")
visp["Dataset ID", "Start Time", "Average Fried Parameter", "Embargoed"][:3]
```

Once we have selected the rows we are interested in we can move onto downloading the ASDF files.

## Downloading Files with `Fido.fetch`

```{note}
Only the ASDF files can be downloaded with `Fido`.
To download the FITS files containing the data, see the [downloading data tutorial](dkist:tutorial:downloading-data)
```

To download files with `Fido` we pass the search results to `Fido.fetch`.

Let's do so with one of our VISP results:
```{code-cell} python
Fido.fetch(visp[0])
```
This will download the ASDF file to the sunpy default data directory `~/sunpy/data`, we can customise this with the `path=` keyword argument.
Note that you can also pass more than one result to be downloaded.

A simple example of both of these is:

```{code-cell} python
Fido.fetch(visp[:3], path="~/dkist_data/{instrument}/{dataset_id}/")
```

This will put each of our ASDF files in a directory named with the corresponding Dataset ID and Instrument.
