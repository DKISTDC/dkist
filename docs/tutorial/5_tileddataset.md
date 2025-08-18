---
jupytext:
  formats: md:myst
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

(dkist:tutorial:tiled-dataset)=
# Working with Tiled Datasets

So far all our examples have used the base {obj}`dkist.Dataset` class with VISP data.
In this way we have demonstrated the most important features of the Python tools for working with DKIST data, but some data do not quite fit into the base `Dataset` structure.
Specifically, VBI and DL-NIRSP data consist of distinct image tiles forming a larger mosaic image.
The individual tiles of the image are not combined by the Data Center into a single image, since this would involve interpolation at the tile edges and this is left to the user to make their own choices about.
Instead the tiles are kept separate but must therefore be considered as separate images by the `Dataset` object.

For this purpose the Python tools have the {obj}`dkist.TiledDataset` class, which is essentially a 2D array of `Dataset` objects, with some helper functions to make it easier to work with those `Dataset`s either individually or together.

To see `TiledDataset` in action we'll load some VBI data. We'll use the VBI data from the sample datasets, which is accessible in the same way as the VISP dataset we used before

```{code-cell} ipython3
---
tags: [keep-inputs]
---
import dkist
from dkist.data.sample import VBI_L1_NZJTB

VBI_L1_NZJTB
```

Now let's use that file path to create a `TiledDataset`. This is done in exactly the same way as for a regular `Dataset`, using `load_dataset()`:

```{code-cell} ipython3
tds = dkist.load_dataset(VBI_L1_NZJTB)
tds
```

You will see that this output looks very similar to the output for our VISP dataset in previous examples.
We still have information about the number and type of pixel and world dimensions in the constituent datasets, and the correlations between them.
(Note: this information is taken from the first tile and assumes it is the same for all tiles.) In this case the output also tells us that this is a 3x3 array of `Dataset`s with 27 frames in total.

Some of this basic information is also available as attributes on the `TiledDataset`, just as it is with `Dataset`. For instance the shape of the array of tiles:

```{code-cell} ipython3
tds.shape
```

This is not to be confused with the shapes of the tiles themselves:

```{code-cell} ipython3
tds.tiles_shape
```

`TiledDataset` also keeps the `.inventory` attribute containing important metadata about the dataset:

```{code-cell} ipython3
tds.inventory
```

And the headers for all the datasets are stored as `combined_headers`:

```{code-cell} ipython3
tds.combined_headers
```

Of course, since `TiledDataset` is array-like, we can also index it to access individual tiles.

```{code-cell} ipython3
tds[0, 0]
```

And there is a `flat` attribute which can be used for things like iterating more easily:

```{code-cell} ipython3
tds.flat[0]
```

```{code-cell} ipython3
for tile in tds.flat:
    print(tile.headers['DATE-AVG'])
```

However, if we want to look at all the component datasets but only a portion of each then we can index with `slice_tiles`. So to get only the first time step of each tile:

```{code-cell} ipython3
tds.slice_tiles[0]
```

Notice that this gives us a new `TiledDataset` with the same number of tiles but smaller datasets.

Similarly if we want to crop the edges of each tile, we can index just as easily in the spatial dimensions:

```{code-cell} ipython3
tds.slice_tiles[:, 1024:-1024, 1024:-1024]
```

## `TiledDataset` objects with missing tiles

As seen above, the default mode for VBI is to take data so that tiles overlap only slightly to form a larger image.
However, some experiments might use an irregular arrangement of tiles with greater overlap.
One common example of this is the main image being composed of four tiles together and a fifth in the centre overlapping all four.
`TiledDataset` exposes this as a regular grid with certain missing tiles masked out.
In this example the tiles would be stored as a 3x3 grid with the middle tile on each edge masked out.

Which tiles should be masked is determined by the `.mask` attribute.

```{code-cell} ipython3
---
tags: [keep-inputs]
---
# Construct an example mask for demonstration with the sample dataset
tds.mask = [[False, True, False], [True, False, True], [False, True, False]]
```

```{code-cell} ipython3
tds
```

Notice that although the `TiledDataset` is still a 3x3 grid, the total number of frames given is 15 rather than 27, because it has skipped the masked tiles (even though in this case the data are still actually there).
Other methods will also skip any masked tiles:

```{code-cell} ipython3
tds.tiles_shape
```

```{code-cell} ipython3
for tile in tds.flat:
	print(tile.headers['DATE-AVG'])
```

+++

However, be careful of iterating over the whole grid of tiles manually, as this will not skip the masked tiles and may break.

```{code-cell} ipython3
---
tags: [raises-exception]
---
for row in tds:
    for tile in row:
        print(tile[0].headers['DATE-AVG'])
```
