---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.17.1
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

+++ {"editable": true, "slideshow": {"slide_type": "slide"}}

# Exercise 1

+++ {"editable": true, "slideshow": {"slide_type": ""}}

Load the sample VISP dataset. **Without actually slicing the dataset**, figure out how many files are in the following slices:

- `ds[0]`
- `ds[:, :200]`
- `ds[:, :200, :200]`
- `ds[:, :, :200, :200]`

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
from dkist import load_dataset
from dkist.data.sample import VISP_L1_KMUPT

ds = load_dataset(VISP_L1_KMUPT)
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
ds.shape
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
ds.files
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
ds[0].files
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
ds[:, :200].files
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
ds[:, :200, :200].files
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
ds[:, :, :200, :200].files
```

+++ {"editable": true, "slideshow": {"slide_type": "slide"}}

# Exercise 2

+++

Find the dataset from this year with the highest number of frames.

- What is the dataset's Product ID?
- How many frames does the dataset have?
- Is the dataset embargoed? If yes, when does the embargo period end?

+++

**Tips:**

- You can pass `a.Provider("dkist")` to `Fido.search()` to search only for data provided by DKIST
- You can use `.keys()` or `.colnames` on a `DKISTQueryResponse` object to see all the column names

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: notes
---
from sunpy.net import attrs as a, Fido
import dkist.net
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
# Search for all DKIST data this year
res = Fido.search(a.Provider("dkist"), a.Time("2025-01-01", "2026-01-01"))
res
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
# Just get the DKIST results table and sort by number of frames, largest first
res2 = res['dkist']
res2 = res[0]
res2
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
res2.sort("Number of Frames", reverse=True)
```

```{code-cell} ipython3
p = res2.copy()
print(p.sort("Number of Frames"))
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
# Print top result, ie dataset with largest number of frames
res2[:5]["Product ID", "Instrument", "Embargoed", "Number of Frames", "Embargo End Date"]
```

```{code-cell} ipython3
max_frames = res[0]["Number of Frames"].max()
max_frames
```

```{code-cell} ipython3
large = res[0][res[0]["Number of Frames"] == max_frames]
large
```

```{code-cell} ipython3
Fido.fetch(large)
```

+++ {"editable": true, "slideshow": {"slide_type": "slide"}}

# Exercise 3

+++ {"editable": true, "slideshow": {"slide_type": ""}}

Open the VBI sample dataset again. Choose two adjacent tiles and calculate the overlap between them in arcseconds.

HINTS:
- You will only need the first from of each tile.
- You may find the `SkyCoord.separation()` method helpful

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
from dkist.data.sample import VBI_L1_NZJTB
from dkist import load_dataset
import astropy.units as u

ds = load_dataset(VBI_L1_NZJTB)
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
# We only need the first image of each tile
first_tiles = ds.slice_tiles[0]
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
# The bottom left tile is 0,0, get the corner pixel on the right side
tile1_bottom_right_pix = first_tiles[0,0].wcs.array_index_to_world(0, 4096)
tile1_bottom_right_pix
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
# The bottom middle tile is 1,0, get the corner pixel on the left side
tile2_bottom_left_pix = first_tiles[1,0].wcs.array_index_to_world(0, 0)
tile2_bottom_left_pix
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
(tile1_bottom_right_pix.separation(tile2_bottom_left_pix).to(u.arcsec),

tile1_bottom_right_pix.Tx - tile2_bottom_left_pix.Tx,

tile1_bottom_right_pix.Ty - tile2_bottom_left_pix.Ty)
```

+++ {"editable": true, "slideshow": {"slide_type": "slide"}}

# Exercise 4

+++ {"editable": true, "slideshow": {"slide_type": ""}}

Using Fido, find the co-temporal VISP dataset, VBI dataset and AIA image from 19:47 on 2024/04/17. Use `sunpy.visualization.drawing.extent` to plot the FOV of the VBI and VISP datasets onto the AIA image.

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
# Download one VISP and one VBI metadata ASDF file and a co-temporal AIA image for 19:47 on 2024-04-17
# Using sunpy.visualization.drawing.extent plot the FOV of the VBi and VISP datasets on the AIA image.
import matplotlib.pyplot as plt

import sunpy.map
from sunpy.net import Fido, attrs as a
from sunpy.visualization import drawing

import dkist
import dkist.net
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
res = Fido.search(a.Time("2024-04-17T19:47:00", "2024-04-17T19:48:00"),
                  a.Instrument.vbi | a.Instrument.visp | a.Instrument.aia)
# Download the first result from each provider
files = Fido.fetch(res[:,0])
files.sort()
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
# Unpack the filenames
vbi_file, visp_file, aia_file = files

# Load VBI and VISP datasets
vbi, visp = dkist.load_dataset((vbi_file, visp_file))

# Load the AIA data
aia = sunpy.map.Map(aia_file)
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
# Create an axes with the AIA data's coordinate frame
fig = plt.figure(figsize=(8,8))
ax = fig.add_subplot(projection=aia)

# Plot the AIA data
aia.plot(axes=ax)

# Draw the extents of the VBI and VISP data
drawing.extent(ax, vbi[0].wcs, color="C1", label="VBI")
drawing.extent(ax, visp[0,:,0,:].wcs, color="C2", label="VISP")

plt.legend()

_ = ax.axis((1000, 2000, 2600, 3400))
```
