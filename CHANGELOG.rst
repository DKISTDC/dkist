0.1.0 (Unreleased)
==================

The initial release of the DKIST Python tools.

New Features
------------

- Add a reader for asdf files [#1]
- Add `dkist.dataset.Dataset` class to represent a dataset to the user [#1]
- Add code for converting a nested list of `asdf.ExternalArrayReference`
  objects to a `dask.array.Array` [#1]
- Add implementation of `dkist.dataset.Dataset.pixel_to_world` and
  `dkist.dataset.Dataset.world_to_pixel` [#1]
- Add ability to crop Dataset array by world coordinates [#1]
- Python 3.6+ Only [#11]

Bug Fixes
---------

