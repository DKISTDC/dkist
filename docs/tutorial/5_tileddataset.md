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

# TiledDataset

So far all our examples have used the base {obj}`dkist.Dataset` class with VISP data.
In this way we have demonstrated the most important features of the Python tools for working with DKIST data, but some data do not quite fit into the base `Dataset` structure.
Specifically, VBI data consist of distinct image tiles forming a larger mosaic image.
The individual tiles of the image are not combined by the Data Center into a single image, since this would involve interpolation at the tile edges and this is left to the user to make their own choices about.
Instead the tiles are kept separate but must therefore be considered as separate images by the `Dataset` object.

For this purpose the Python tools have the {obj}`dkist.TiledDataset` class, which is essentially a 2D array of `Dataset` objects, with some helper functions to make it easier to work with those `Dataset`s either individually or together.

To see `TiledDataset` in action we'll load some VBI data. We've already seen how to search for and download data, so we won't cover this again here. Instead, we will use one of the sample datasets distributed with the Python tools.


```{code-cell} ipython3
import dkist
from dkist.data.sample import VBI_AJQWW

VBI_AJQWW
```

This constant defines the path to a folder containing the metadata ASDF and a few data files for a small VBI dataset.
These are automatically downloaded as a .tar file and unpacked the first time you import the sample data so that the dataset is always available.

Now let's use that file path to create a `TiledDataset`. This is done in exactly the same way as for a regular `Dataset`, using `load_dataset()`:


```{code-cell} ipython3
tds = dkist.load_dataset(VBI_AJQWW)
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

Similarly if we want to crop the edges of each tile we can index just as easily in the spatial dimensions:


```{code-cell} ipython3
tds.slice_tiles[:, 1024:-1024, 1024:-1024]
```
