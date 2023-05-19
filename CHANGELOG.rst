1.0.0b13 (2023-05-19)
=====================

Features
--------

- Add support for passing a list of dataset IDs as strings to `dkist.net.transfer_complete_datasets`. (`#240 <https://github.com/DKISTDC/dkist/pull/240>`_)


Bug Fixes
---------

- Fix errors with some types of input in `dkist.net.transfer_complete_datasets`. (`#240 <https://github.com/DKISTDC/dkist/pull/240>`_)
- Fix searching for Globus endpoints with SDK 3 (`#240 <https://github.com/DKISTDC/dkist/pull/240>`_)
- Fixes bug in the inverse property of CoupledCompoundModel by correcting the various mappings in the inverse. (`#242 <https://github.com/DKISTDC/dkist/pull/242>`_)


1.0.0b12 (2023-05-16)
=====================

Features
--------

- Drop support for Python 3.8 in line with `NEP 29 <https://numpy.org/neps/nep-0029-deprecation_policy.html>_`. (`#232 <https://github.com/DKISTDC/dkist/pull/232>`_)
- Add new methods `.FileManager.quality_report()` and `.FileManager.preview_movie()` to download the quality report and preview movie. These are accessed as ``Dataset.files.quality_report`` and ``Dataset.files.preview_movie``. (`#235 <https://github.com/DKISTDC/dkist/pull/235>`_)


Bug Fixes
---------

- Unit for ``lon_pole`` was set to the spatial unit of the input parameters within `~dkist.wcs.models.VaryingCelestialTransform`.
  It is now fixed to always be degrees. (`#225 <https://github.com/DKISTDC/dkist/pull/225>`_)
- Add a new model to take a 2D index and return the corresponding correct index for a 1D array, and the inverse model for the reverse operation.
  To be used as a compound with Tabular1D so that it looks like a Tabular2D but the compound model can still be inverted. (`#227 <https://github.com/DKISTDC/dkist/pull/227>`_)


Trivial/Internal Changes
------------------------

- Internal improvements to how the data are loaded from the collection of FITS files.
  This should have no user facing effects, but provides a foundation for future performance work. (`#232 <https://github.com/DKISTDC/dkist/pull/232>`_)


1.0.0b11 (2023-02-15)
=====================

Features
--------

- Add ability to page through the DKIST results and affect the page size. (`#212 <https://github.com/DKISTDC/dkist/pull/212>`_)
- Fix, and make requried, the unit property on a dataset in ASDF files. (`#221 <https://github.com/DKISTDC/dkist/pull/221>`_)


Bug Fixes
---------

- Fix bugs in testing caused by the release of ``pytest 7.2.0``. (`#210 <https://github.com/DKISTDC/dkist/pull/210>`_)
- Make loading a mosaiced VBI dataset work with `Dataset.from_asdf`. (`#213 <https://github.com/DKISTDC/dkist/pull/213>`_)
- Add support for Python 3.11 (`#218 <https://github.com/DKISTDC/dkist/pull/218>`_)


Improved Documentation
----------------------

- Add documentation for available path interpolation keys. (`#207 <https://github.com/DKISTDC/dkist/pull/207>`_)


1.0.0b9 (2022-09-30)
====================

Features
--------

- Add a ``label=`` kwarg to `.FileManager.download` and
  `.transfer_complete_datasets` allowing the user to completely customise the
  Globus transfer task label. (`#193 <https://github.com/DKISTDC/dkist/pull/193>`_)


Bug Fixes
---------

- Successfully ask for re-authentication when Globus token is stale. (`#197 <https://github.com/DKISTDC/dkist/pull/197>`_)
- Fix a bug where ``FileManager.download`` would fail if there was not an
  asdf file or quality report PDF in inventory. (`#199 <https://github.com/DKISTDC/dkist/pull/199>`_)
- Fix an issue with slicing a dataset where the slicing wouldn't work correctly
  if the first axis of the data array has length one. (`#199 <https://github.com/DKISTDC/dkist/pull/199>`_)
- No more invalid characters in default Globus label name. (`#200 <https://github.com/DKISTDC/dkist/pull/200>`_)
- Hide extraneous names in `dkist.net.attrs` with underscores so they don't get imported when using that module. (`#201 <https://github.com/DKISTDC/dkist/pull/201>`_)
- Catch empty return value from data search in `transfer_complete_datasets` and raise a ValueError telling the user what's happening. (`#204 <https://github.com/DKISTDC/dkist/pull/204>`_)


v1.0.0b8 (2022-07-18)
=====================

Features
--------

- Support passing a whole `~sunpy.net.fido_factory.UnifiedResponse` to
  `dkist.net.transfer_complete_datasets`. (`#165 <https://github.com/DKISTDC/dkist/pull/165>`_)
- Support pretty formatting of new Dataset Inventory fields in Fido search
  results table. (`#165 <https://github.com/DKISTDC/dkist/pull/165>`_)


Bug Fixes
---------

- Refactor `.FileManager` to correctly support slicing. (`#176 <https://github.com/DKISTDC/dkist/pull/176>`_)
- Unify path handling between `.FileManager.download` and `.DKISTClient.fetch`.
  This means that you can use the same path specification to download the ASDF
  files and the FITS files, using keys such as "Dataset ID". (`#178 <https://github.com/DKISTDC/dkist/pull/178>`_)


v1.0.0b7 (2022-05-10)
=====================

Features
--------

- Use the new ``/datasets/v1/config`` endpoint to automatically retrieve the globus endpoint ID corresponding to the dataset searcher in use. (`#136 <https://github.com/DKISTDC/dkist/pull/136>`_)
- Add a new function `dkist.net.transfer_complete_datasets` which takes a single row from a ``Fido`` search or a dataset ID and sets up a Globus transfer task for the complete dataset. (`#136 <https://github.com/DKISTDC/dkist/pull/136>`_)
- Migrate to Globus SDK version 3+. Also use the config system to configure endpoints for dataset search and metadata download. (`#136 <https://github.com/DKISTDC/dkist/pull/136>`_)


Trivial/Internal Changes
------------------------

- Rename ``dkist.net.DKISTDatasetClient`` to ``dkist.net.DKISTClient``. The only user facing change this has is to modify the key used when slicing the return from ``Fido.search``. (`#136 <https://github.com/DKISTDC/dkist/pull/136>`_)


v1.0.0b6 (2022-03-30)
=====================

Features
--------

- Implement models where the pointing varies along the second pixel axis (for
  rastering slit spectrographs). (`#161 <https://github.com/DKISTDC/dkist/pull/161>`_)


Bug Fixes
---------

- Fix behaviour of `VaryingCelestialTransform` when called with arrays of pixel or world coordinates. (`#160 <https://github.com/DKISTDC/dkist/pull/160>`_)


v1.0.0b4 (2022-02-16)
=====================

Features
--------

- Implement Astropy models to support spatial transforms which change with
  a thrid pixel axis. (`#148 <https://github.com/DKISTDC/dkist/pull/148>`_)
- Add ASDF serialization for `VaryingCelestialTransform` and `CoupledCompoundModel`. (`#156 <https://github.com/DKISTDC/dkist/pull/156>`_)


Bug Fixes
---------

- Fix asdf using old schema and tag versions when saving new files. (`#157 <https://github.com/DKISTDC/dkist/pull/157>`_)


Trivial/Internal Changes
------------------------

- Migate to the asdf 2.8+ ``Converter`` interface, this bumps various
  dependancies but should have no effect on reading or writing asdf files. (`#152 <https://github.com/DKISTDC/dkist/pull/152>`_)


v1.0.0b3 (2021-11-30)
=====================

Features
--------

- The inventory record and the headers table are now both stored in the
  ``Dataset.meta`` dict rather than headers being it's own attribute. This means
  it is more likely to be carried through correctly when doing operations
  designed for ``NDCube`` objects. (`#139 <https://github.com/DKISTDC/dkist/pull/139>`_)
- Add support for tiled datasets in the spatial dimensions.
  This adds a new class `dkist.TiledDataset` which holds a 2D grid of `dkist.Dataset`
  objects, and associated asdf schemas to serialise them. (`#143 <https://github.com/DKISTDC/dkist/pull/143>`_)


1.0.0b1 (2021-09-15)
====================

Features
--------

- Move file handling and download tooling onto `.Dataset.files`, which is now
  a pointer to a class which has all the information to generate the arrays.

  Also the loaders generated by the new `.FileManager` class now have a reference
  to the `.FileManager` which generated them, which means that the basepath can
  be dynamically generated by reference. (`#126 <https://github.com/DKISTDC/dkist/pull/126>`_)
- Modify the `dkist.io.FileManager` class so that most of the functionality
  exists in the new base class and the dowload method is in the separate child
  class. In addition make more of the API private to not confuse end users. (`#130 <https://github.com/DKISTDC/dkist/pull/130>`_)


Improved Documentation
----------------------

- Write initial guide to the user tools and tidy up the API docs (`#127 <https://github.com/DKISTDC/dkist/pull/127>`_)


0.1a6 (2021-07-05)
==================

Bug Fixes
---------

- Fix a bug where sometimes the path wouldn't be set correctly after FITS file download. (`#124 <https://github.com/DKISTDC/dkist/pull/124>`_)


0.1a5 (2021-06-29)
==================

Bug Fixes
---------

- Fix display of sliced datasets in repr and correctly propagate slicing operations to the array container. (`#119 <https://github.com/DKISTDC/dkist/pull/119>`_)


0.1a4 (2021-05-19)
==================

Features
--------

- Implement `DKISTClient.fetch` to download asdf files from the metadata
  streamer service. (`#90 <https://github.com/DKISTDC/dkist/pull/90>`_)
- Enable tests on Windows (`#95 <https://github.com/DKISTDC/dkist/pull/95>`_)
- Added search bounding box functionality to DKIST client. (`#100 <https://github.com/DKISTDC/dkist/pull/100>`_)
- Added support for new dataset search parameters (``hasSpectralAxis``, ``hasTemporalAxis``, ``averageDatasetSpectralSamplingMin``, ``averageDatasetSpectralSamplingMax``, ``averageDatasetSpatialSamplingMin``, ``averageDatasetSpatialSamplingMax``, ``averageDatasetTemporalSamplingMin``, ``averageDatasetTemporalSamplingMax``) (`#108 <https://github.com/DKISTDC/dkist/pull/108>`_)


Trivial/Internal Changes
------------------------

- Support gwcs 0.14 and ndcube 2.0.0b1 (`#86 <https://github.com/DKISTDC/dkist/pull/86>`_)
- Update Fido client for changes in sunpy 2.1; bump the sunpy dependancy to at
  least 2.1rc3. (`#89 <https://github.com/DKISTDC/dkist/pull/89>`_)


v0.1a2 (2020-04-29)
===================

Features
--------

- Move asdf generation code into dkist-inventory package (`#79 <https://github.com/DKISTDC/dkist/pull/79>`_)


v0.1a1 (2020-03-27)
===================

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
