Dkist 0.1a4 (2021-05-19)
========================

Features
--------

- Implement `DKISTDatasetClient.fetch` to download asdf files from the metadata
  streamer service. (`#90 <https://github.com/DKISTDC/dkist/pull/90>`_)
- Enable tests on Windows (`#95 <https://github.com/DKISTDC/dkist/pull/95>`_)
- Added search bounding box functionality to DKIST client. (`#100 <https://github.com/DKISTDC/dkist/pull/100>`_)
- Added support for new dataset search parameters (``hasSpectralAxis``, ``hasTemporalAxis``, ``averageDatasetSpectralSamplingMin``, ``averageDatasetSpectralSamplingMax``, ``averageDatasetSpatialSamplingMin``, ``averageDatasetSpatialSamplingMax``, ``averageDatasetTemporalSamplingMin``, ``averageDatasetTemporalSamplingMax``) (`#108 <https://github.com/DKISTDC/dkist/pull/108>`_)


Trivial/Internal Changes
------------------------

- Support gwcs 0.14 and ndcube 2.0.0b1 (`#86 <https://github.com/DKISTDC/dkist/pull/86>`_)
- Update Fido client for changes in sunpy 2.1; bump the sunpy dependancy to at
  least 2.1rc3. (`#89 <https://github.com/DKISTDC/dkist/pull/89>`_)


Dkist v0.1a2 (2020-04-29)
=========================

Features
--------

- Move asdf generation code into dkist-inventory package (`#79 <https://github.com/DKISTDC/dkist/pull/79>`_)


Dkist v0.1a1 (2020-03-27)
=========================

Backwards Incompatible Changes
------------------------------

- Move the `dkist.asdf_maker` package to `dkist.io.asdf.generator` while also refactoring its internal structure to hopefully make it a little easier to follow. (`#71 <https://github.com/DKISTDC/dkist/pull/71>`_)


Features
--------

- Add `dkist.dataset.Dataset` class to represent a dataset to the user. (`#1 <https://github.com/DKISTDC/dkist/pull/1>`_)
- Add code for converting a nested list of `asdf.ExternalArrayReference` objects to a `dask.array.Array`. (`#1 <https://github.com/DKISTDC/dkist/pull/1>`_)
- Add implementation of `dkist.dataset.Dataset.pixel_to_world` and `dkist.dataset.Dataset.world_to_pixel`. (`#1 <https://github.com/DKISTDC/dkist/pull/1>`_)
- Add ability to crop Dataset array by world coordinates. (`#1 <https://github.com/DKISTDC/dkist/pull/1>`_)
- Add a reader for asdf files. (`#1 <https://github.com/DKISTDC/dkist/pull/1>`_)
- Add a dkist config file using custom location from astropy (`#3 <https://github.com/DKISTDC/dkist/pull/3>`_)
- Add functionality for making asdf files from collections of calibrated FITS
  files. (`#10 <https://github.com/DKISTDC/dkist/pull/10>`_)
- Python 3.6+ Only. (`#11 <https://github.com/DKISTDC/dkist/pull/11>`_)
- Add framework for slicing gwcses. (`#18 <https://github.com/DKISTDC/dkist/pull/18>`_)
- Implement dataset slicing. This orders the results of WCS related methods on
  the dataset class in reverse order to that of the underlying WCS. So it is not
  so jarring that the array and WCS are in reverse order. (`#20 <https://github.com/DKISTDC/dkist/pull/20>`_)
- Add a ``dataset_from_fits`` function that generates an asdf file in a directory
  with a set of FITS files. (`#21 <https://github.com/DKISTDC/dkist/pull/21>`_)
- Add support for array wcs calls post slicing a non-separable dimension. (`#23 <https://github.com/DKISTDC/dkist/pull/23>`_)
- Add ``relative_to`` kwarg to `dkist.asdf_maker.generator.dataset_from_fits` and `dkist.asdf_maker.generator.asdf_tree_from_filenames`. (`#26 <https://github.com/DKISTDC/dkist/pull/26>`_)
- Add support for 2D plotting with WCSAxes. (`#27 <https://github.com/DKISTDC/dkist/pull/27>`_)
- All asdf files are now validated against the level 1 dataset schema on save and load. (`#41 <https://github.com/DKISTDC/dkist/pull/41>`_)
- Add support for returning an array of NaNs when the file is not present. This is needed to support partial dataset download from the DC. (`#43 <https://github.com/DKISTDC/dkist/pull/43>`_)
- Add utilities for doing OAuth with Globus. (`#46 <https://github.com/DKISTDC/dkist/pull/46>`_)
- Add helper functions for listing a globus endpoint (`#49 <https://github.com/DKISTDC/dkist/pull/49>`_)
- Add support for multiple globus oauth scopes (`#50 <https://github.com/DKISTDC/dkist/pull/50>`_)
- Added support for starting and monitoring Globus transfer tasks (`#55 <https://github.com/DKISTDC/dkist/pull/55>`_)
- Allow easy access to the filenames contained in an
  `dkist.io.BaseFITSArrayContainer` object via a `~dkist.io.BaseFITSArrayContainer.filenames` property. (`#56 <https://github.com/DKISTDC/dkist/pull/56>`_)
- `dkist.io.BaseFITSArrayContainer` objects are now sliceable. (`#56 <https://github.com/DKISTDC/dkist/pull/56>`_)
- Initial implementation of `dkist.Dataset.download` method for transferring
  files via globus (`#57 <https://github.com/DKISTDC/dkist/pull/57>`_)
- Rely on development NDCube 2 for all slicing and plotting code (`#60 <https://github.com/DKISTDC/dkist/pull/60>`_)
- Change Level 1 asdf layout to use a tag and schema for ``Dataset``. This allows
  reading of asdf files independant from the `dkist.Dataset` class. (`#66 <https://github.com/DKISTDC/dkist/pull/66>`_)
- Implement a new more efficient asdf schema and tag for `dkist.io.array_containers.BaseFITSArrayContainer` to massively improve asdf load times. (`#70 <https://github.com/DKISTDC/dkist/pull/70>`_)
- Add a `sunpy.net.Fido` client for searching DKIST Dataset inventory. Currently only supports search. (`#73 <https://github.com/DKISTDC/dkist/pull/73>`_)
- Implement correct extraction of dataset inventory from headers and gwcs. Also
  updates some data to be closer to the in progress outgoing header spec (214) (`#76 <https://github.com/DKISTDC/dkist/pull/76>`_)


Bug Fixes
---------

- Fix the units in `spatial_model_from_header` (`#19 <https://github.com/DKISTDC/dkist/pull/19>`_)
- Correctly parse headers when generating gwcses so that only values that change
  along that physical axis are considered. (`#21 <https://github.com/DKISTDC/dkist/pull/21>`_)
- Reverse the ordering of gWCS objects generated by ``asdf_helpers`` as they are
  cartesian ordered not numpy ordered (`#21 <https://github.com/DKISTDC/dkist/pull/21>`_)
- Fix incorrect compound model tree splitting when the split needed to happen at the top layer (`#23 <https://github.com/DKISTDC/dkist/pull/23>`_)
- Fix a lot of bugs in dataset generation and wcs slicing. (`#24 <https://github.com/DKISTDC/dkist/pull/24>`_)
- Fix incorrect chunks when creating a dask array from a loader_array. (`#26 <https://github.com/DKISTDC/dkist/pull/26>`_)
- Add support for dask 2+ and make that the minmum version (`#68 <https://github.com/DKISTDC/dkist/pull/68>`_)


Trivial/Internal Changes
------------------------

- Migrate the `dkist.dataset.Dataset` class to use gWCS's APE 14 API (`#32 <https://github.com/DKISTDC/dkist/pull/32>`_)
