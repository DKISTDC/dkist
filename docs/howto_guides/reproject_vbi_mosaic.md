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

# Stitching a VBI Mosaic with `reproject`

```{note}
You will need the reproject and shapely packages installed to run this guide.

If you have installed `dkist` with pip you may need to run `pip install 'reproject[all]'` to install shapely as an optional dependency for reproject. If you installed with conda you may need to run `conda install shapely`.
```

The [reproject](https://reproject.readthedocs.io/) package is an Astropy-affiliated package for regridding data.
A number of different algorithms are implemented in the package, with different trade-offs for speed and accuracy.
Reprojecting a single spatial image such as an AIA image is well supported and demonstrated in the [sunpy gallery](https://docs.sunpy.org/en/latest/generated/gallery/index.html#combining-co-aligning-and-reprojecting-images).

We are going to use the example of using reproject's {obj}`reproject.mosaicking.reproject_and_coadd` function to stitch a mosaic of VBI frames.


## Obtaining some data

First, we must obtain the VBI data needed for the rest of the guide.

```{code-cell} ipython3
import numpy as np
import matplotlib.pyplot as plt
import astropy.units as u

from sunpy.net import Fido, attrs as a

import dkist
import dkist.net
```

```{code-cell} ipython3
res = Fido.search(a.dkist.Dataset("AJQWW"), )
res
```

```{code-cell} ipython3
asdf_file = Fido.fetch(res, path="~/dkist_data/{dataset_id}")
asdf_file
```

This gives us a {obj}`dkist.TiledDataset` object, which is an array of {obj}`dkist.Dataset` objects.

```{code-cell} ipython3
ds = dkist.load_dataset(asdf_file)
ds
```

To start off, let's just download the first frame of each tile.

```{code-cell} ipython3
first_tiles = [tile[0] for tile in ds.flat]
```

```{code-cell} ipython3
:tags: [skip-execution]

for i, tile in enumerate(first_tiles):
    # Wait for only the last download to finish
    tile.files.download(wait=i == len(first_tiles) - 1)
```

We can now make a composite plot of all the tiles.

```{code-cell} ipython3
fig = plt.figure(figsize=(12, 12))

for i, tile in enumerate(first_tiles):
    ax = fig.add_subplot(ds.shape[0], ds.shape[1], i+1, projection=tile.wcs)
    ax.set_title(f"MINDEX1={tile.headers[0]['MINDEX1']}, MINDEX2={tile.headers[0]['MINDEX2']}")
    ax.imshow(tile.data)

fig.tight_layout()
```

## Regridding with Reproject

```{code-cell} ipython3
from reproject.mosaicking import find_optimal_celestial_wcs, reproject_and_coadd
from reproject import reproject_interp

from ndcube import NDCube
```

First, let us crop off the edges of all our tiles to remove some artifacts.

```{code-cell} ipython3
first_tiles = [d[0, 100:-100, 100:-100] for d in ds.flat]
```

Next we need to calculate the optimal WCS for the output:

```{code-cell} ipython3
reference_wcs, shape_out = find_optimal_celestial_wcs(
    [f.wcs for f in first_tiles],
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
    first_tiles,
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
