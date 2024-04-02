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

# Spatial Bounding Boxes of VISP Datasets

```{note}
You will sunpy's Map submodule to run this example, if you installed dkist from pip you may need to run `pip install sunpy[all]`.
If you installed with conda you will already have it installed.
```

In this example we will demonstrate how to view the bounding box of a VISP dataset on an AIA image.

The first step is to download an ASDF file for the VISP dataset and a cotemporal AIA image.
We are assuming we know the time range of interest, and only want one passband of AIA.

```{code-cell} ipython3
import astropy.units as u

from sunpy.net import Fido, attrs as a

import dkist
import dkist.net

results = Fido.search(a.Time("2023/10/16 18:45", "2023/10/16 18:48"), (a.Instrument.visp | (a.Instrument.aia & a.Wavelength(17.1*u.nm))))
results
```

This search gets us data from three arms of VISP as well as many AIA images, let's only download the first results from each search.

```{code-cell} ipython3
files = Fido.fetch(results[:, 0])
files
```

Now we load the first file into a `dkist.Dataset` object and the second into a sunpy `Map`.

```{code-cell} ipython3
ds = dkist.load_dataset(files[0])
ds
```

```{code-cell} ipython3
import sunpy.map

aia = sunpy.map.Map(files[1])
aia
```

To plot the spatial bounding box of the VISP dataset, we crop out all the non-spatial axes. In this case we pick the 0th Stokes and wavelength axis so we are left with a two dimensional dataset.

```{code-cell} ipython3
visp_spatial = ds[0, :, 0, :]
visp_spatial
```

We can now extract the bottom left and top right corners of the VISP data by finding the world coordinates of the bottom left pixel and top right pixel.
```{note}
Note that we subtract 0.5 from the data shape, this is because we want to find the coordinate of the center of the pixel not the edge.
```

```{code-cell} ipython3
corners = visp_spatial.wcs.array_index_to_world([0, visp_spatial.data.shape[0] - 0.5],
                                                [0, visp_spatial.data.shape[1] - 0.5])
corners
```

You will also see how this call returns the extent of the times for the raster scan, because we only want the spatial coordinates we shall just extract the `SkyCoord` object.

```{code-cell} ipython3
corners = corners[0]
```

We can now plot the AIA image as a [sunpy Map](https://docs.sunpy.org/en/stable/tutorial/maps.html) and then draw a rectangle with our corners.

```{code-cell} ipython3
import matplotlib.pyplot as plt

ax = plt.subplot(projection=aia)
aia.plot(axes=ax)
aia.draw_quadrangle(corners)
```
