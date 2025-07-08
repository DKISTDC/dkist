---
jupytext:
  formats: md:myst,ipynb
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

(dkist:examples:visp-extents)=
# Showing the Field of View of VISP on AIA

```{code-cell} ipython3
import numpy as np
import matplotlib.pyplot as plt
import astropy.units as u
from astropy.time import Time

import sunpy.map
from sunpy.net import Fido, attrs as a
from sunpy.visualization import drawing

import dkist
import dkist.net
from dkist.data.sample import VISP_BKPLX
```

```{note}
This example requires `sunpy>=6.1` for the {obj}`sunpy.visualization.extent` function.
```

+++

## Obtaining some data

In this example we will use the VISP sample dataset [BKPLX](https://dkist.data.nso.edu/datasetview/BKPLX).
If you want to replace this dataset with your own dataset, see {ref}`dkist:howto-guide:sample-data`.

Let's load the data with {obj}`dkist.load_dataset`:

```{code-cell} ipython3
ds = dkist.load_dataset(VISP_BKPLX)
ds
```

Extract the two pixel axes which are correlated to the spatial dimensions, (raster scan step number and spatial along slit).

This VISP dataset only has one raster, if you are using a dataset with repeated rasters, you can either pick one or you can iterate over all the raster repeats to plot the field of view for each one.

```{code-cell} ipython3
spatial_slice = ds[0, :, 0, :]
spatial_slice
```

Extract the times of all the raster positions

```{code-cell} ipython3
times = spatial_slice.axis_world_coords("time")[0]
```

And then download the AIA image closest to the time of the first raster position.

```{code-cell} ipython3
results = Fido.search(a.Instrument.aia, a.Wavelength(171*u.AA), a.Time(times[0], times[-1], times[0]))
results
```

```{code-cell} ipython3
aia_files = Fido.fetch(results, site="NSO")
```

Now we load the downloaded AIA file into a {obj}`sunpy.map.AIAMap` object.

```{code-cell} ipython3
aia = sunpy.map.Map(aia_files)
```

```{code-cell} ipython3
aia
```

Finally we can use a combination of {obj}`sunpy.map.GenericMap.plot` and {obj}`sunpy.visualization.drawing.extent` to plot the extent of the VISP raster.

```{code-cell} ipython3
fig = plt.figure(figsize=(8,8))
ax = fig.add_subplot(projection=aia)

aia.plot(axes=ax)

drawing.extent(ax, spatial_slice.wcs)

# Zoom in on the VBI region using pixel coordinates
_ = ax.axis((1500, 2000, 1900, 2400))
```

```{code-cell} ipython3

```
