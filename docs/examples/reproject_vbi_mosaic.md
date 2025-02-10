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

(dkist:examples:vbi-reproject)=
# Stitching a VBI Mosaic with `reproject`

```{note}
You will need the reproject and shapely packages installed to run this guide.

If you have installed `dkist` with pip you may need to run `pip install 'reproject[all]'` to install shapely as an optional dependency for reproject. If you installed with conda you may need to run `conda install shapely`.
```

The [reproject](https://reproject.readthedocs.io/) package is an Astropy-affiliated package for regridding data.
A number of different algorithms are implemented in the package, with different trade-offs for speed and accuracy.
Reprojecting a single spatial image such as an AIA image is well supported and demonstrated in the [sunpy gallery](https://docs.sunpy.org/en/latest/generated/gallery/index.html#combining-co-aligning-and-reprojecting-images).

We are going to use the example of using reproject's {obj}`reproject.mosaicking.reproject_and_coadd` function to stitch a mosaic of VBI frames.

```{code-cell} ipython3
import numpy as np
import matplotlib.pyplot as plt
import astropy.units as u

import dkist
from dkist.data.sample import VBI_AJQWW
```

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

We can now make a composite plot of all the tiles, at the first timestep.

```{code-cell} ipython3
fig = plt.figure(figsize=(12, 12))
fig = ds.plot(slice_index=0, share_zscale=True)
```

## Regridding with Reproject

```{code-cell} ipython3
from reproject.mosaicking import find_optimal_celestial_wcs, reproject_and_coadd
from reproject import reproject_interp

from ndcube import NDCube
```

First, let us crop off the edges of all our tiles to remove some artifacts, and only select the first time step.
To do this we use the {obj}`.TiledDataset.slice_tiles` helper which applies an array slice to each tile of the {obj}`.TiledDataset` object.

```{code-cell} ipython3
first_tiles = ds.slice_tiles[0, 100:-100, 100:-100]
```

Next we need to calculate the optimal WCS for the output:

```{code-cell} ipython3
reference_wcs, shape_out = find_optimal_celestial_wcs(
    [f.wcs for f in first_tiles.flat],
    auto_rotate=True,
    # We drop the output resolution by a factor of 10 to reduce memory
    # remove this line to run at the native resolution of the input data
    resolution=0.1*u.arcsec,
)

# Due to a bug in reproject we need to reverse the direction of the longitude axis
# https://github.com/astropy/reproject/issues/431
reference_wcs.wcs.cdelt[0] = -reference_wcs.wcs.cdelt[0]
```

Now we can do the actual reprojection

```{code-cell} ipython3
arr, footprint = reproject_and_coadd(
    first_tiles.flat,
    reference_wcs,
    reproject_function=reproject_interp,
    shape_out=shape_out,
    roundtrip_coords=False,
)
```

Make a new `NDCube` object and plot it.

```{code-cell} ipython3
plt.figure(figsize=(10,10))
stitched = NDCube(arr, reference_wcs)
stitched.plot()
```
