---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.6
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

(dkist:examples:vbi-extents)=
# Showing the Field of View of VBI on AIA

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
from dkist.data.sample import VBI_AJQWW
```

```{note}
This example requires `sunpy>=6.1` for the {obj}`sunpy.visualization.extent` function.
```

+++

## Obtaining some data

In this example we will use the VBI sample dataset [AJQWW](https://dkist.data.nso.edu/datasetview/AJQWW).
If you want to replace this dataset with your own dataset, see {ref}`dkist:howto-guide:sample-data`.

Let's load the data with {obj}`dkist.load_dataset`:

```{code-cell} ipython3
ds = dkist.load_dataset(VBI_AJQWW)
ds
```

This gives us a {obj}`dkist.TiledDataset` object, which is an array of {obj}`dkist.Dataset` objects, as this VBI dataset is tiled in space (or mosaiced).

The sample data includes the ASDF file along with the FITS files for the first frame in each mosaic position.

First, let's extract the tiles which make up the first mosaic.

```{code-cell} ipython3
first_tiles = ds.slice_tiles[0]
```

```{code-cell} ipython3
fig = plt.figure(figsize=(12, 12))
fig = ds.plot(0, share_zscale=True, figure=fig)
```

Now let's extract the timestamps of each of these tiles

```{code-cell} ipython3
times = Time([d.global_coords["time"] for d in first_tiles.flat]).sort()
```

And then download the AIA image closest to the time of the first tile within the range of all 9 tiles.

```{code-cell} ipython3
results = Fido.search(a.Instrument.aia, a.Wavelength(171*u.AA), a.Time(times[0], times[-1], times[0]))
results
```

```{code-cell} ipython3
aia_files = Fido.fetch(results)
```

Now we load the downloaded AIA file into a {obj}`sunpy.map.AIAMap` object.

```{code-cell} ipython3
aia = sunpy.map.Map(aia_files)
```

```{code-cell} ipython3
aia
```

Finally we can use a combination of {obj}`sunpy.map.GenericMap.plot` and {obj}`sunpy.visualization.drawing.extent` to plot the extent of each tile on the disk.

```{code-cell} ipython3
fig = plt.figure(figsize=(8,8))
ax = fig.add_subplot(projection=aia)

aia.plot(axes=ax)

# Iterate over each tile plotting the extent of the WCS for each one
for i, tile in enumerate(first_tiles.flat):
    drawing.extent(ax, tile.wcs, color=f"C{i}")

# Zoom in on the VBI region using pixel coordinates
_ = ax.axis((1500, 2000, 1900, 2400))
```
