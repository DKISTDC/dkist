1.5.0 (2024-04-03)
==================

Features
--------

- Our minimum Python version is now 3.10 inline with `SPEC-0 <https://scientific-python.org/specs/spec-0000/>`__. (`#347 <https://github.com/DKISTDC/dkist/pull/347>`_)


Bug Fixes
---------

- Fix broadcasting issues during pixel -> world conversion for models with a Ravel component. (`#309 <https://github.com/DKISTDC/dkist/pull/309>`_)
- Fix a performance regression when dask>=2024.2.1 is installed. (`#361 <https://github.com/DKISTDC/dkist/pull/361>`_)


Improved Documentation
----------------------

- Add a how to guide describing how to reproject VBI data. Also migrate tutorial to the latest DDT datasets. (`#349 <https://github.com/DKISTDC/dkist/pull/349>`_)


Trivial/Internal Changes
------------------------

- Refactor various subclasses of VaryingCelestialTransform to centralise the calculations in preparation for improving performance. (`#344 <https://github.com/DKISTDC/dkist/pull/344>`_)


1.4.0 (2024-02-26)
==================

Bug Fixes
---------

- Correct Fido time searching to use `endTimeMin` and `startTimeMax` (in the correct order) so that searching returns any dataset with a partially or completely overlapping time range. (`#336 <https://github.com/DKISTDC/dkist/pull/336>`_)


Trivial/Internal Changes
------------------------

- Adjust file loading to support single-frame datasets with no time axis. (`#335 <https://github.com/DKISTDC/dkist/pull/335>`_)


1.3.0 (2024-02-19)
==================

Features
--------

- Call the DKIST search API to automatically determine valid data search parameters and register those with the Fido client. (`#311 <https://github.com/DKISTDC/dkist/pull/311>`_)
- Use a new feature in the DKIST datasets API to search for all datasets which intersect the given time. (`#326 <https://github.com/DKISTDC/dkist/pull/326>`_)


Improved Documentation
----------------------

- Fix some small issues with the installation instructions. (`#323 <https://github.com/DKISTDC/dkist/pull/323>`_)


1.2.1 (2024-01-30)
==================

Bug Fixes
---------

- Fix some deprecation warnings for Python 3.12 support. (`#322 <https://github.com/DKISTDC/dkist/pull/322>`_)


1.2.0 (2024-01-29)
==================

Features
--------

- Add a logging framework to present information to users in a nicer way.
  The logger can be accessed as ``dkist.log`` to change log levels etc. (`#317 <https://github.com/DKISTDC/dkist/pull/317>`_)


Bug Fixes
---------

- Bump minimum version of asdf to 2.11.2 to pick up jsonschema bugfix. (`#313 <https://github.com/DKISTDC/dkist/pull/313>`_)
- Change the ``appdirs`` dependency for the maintained ``platformdirs`` package. (`#318 <https://github.com/DKISTDC/dkist/pull/318>`_)
- Fix an unpinned minimum version of ``asdf-wcs-schemas`` causing potential read errors on newest asdf files with dkist 1.1.0. (`#320 <https://github.com/DKISTDC/dkist/pull/320>`_)


1.1.0 (2023-10-27)
==================

Backwards Incompatible Changes
------------------------------

- We now require gwcs 0.19+ and therefore astropy 5.3+ (`#305 <https://github.com/DKISTDC/dkist/pull/305>`_)


Features
--------

- Add a new ``AsymmetricMapping`` model to allow a different mapping in the forward and reverse directions. (`#305 <https://github.com/DKISTDC/dkist/pull/305>`_)


Bug Fixes
---------

- Fix the oversight where, when generating a model for a celestial WCS, the scale model was put before the affine transform in the pipeline. This means that the units for the affine transform matrix provided to ``VaryingCelestialTransform`` and ``generate_celestial_transform`` should be pixels not degrees. (`#305 <https://github.com/DKISTDC/dkist/pull/305>`_)
- Fix missing references to parent transform schemas in ``Ravel`` and ``VaryingCelestialTransform`` ASDF schemas. (`#305 <https://github.com/DKISTDC/dkist/pull/305>`_)


Trivial/Internal Changes
------------------------

- To improve compatibility with external libraries that provide ASDF serialization and
  validation (like asdf-astropy) dkist schemas were updated to use tag wildcards
  when checking tagged objects (instead of requiring specific tag versions). (`#308 <https://github.com/DKISTDC/dkist/pull/308>`_)


v1.0.1 (2023-10-13)
===================

Backwards Incompatible Changes
------------------------------

- The ASDF files currently being served by the data center are incompatible with
  gwcs 0.19+. This is due to a change in how Stokes coordinates are represented.
  In this release we have pinned the gwcs version to <0.19. A future release will
  require 0.19+ when the ASDF files have been updated. (`#301 <https://github.com/DKISTDC/dkist/pull/301>`_)


Bug Fixes
---------

- Add missing dependencies to setup.cfg - explicit is better than implicit. (`#294 <https://github.com/DKISTDC/dkist/pull/294>`_)
- Import ValidationError from asdf, drop jsonschema as a dependency. (`#295 <https://github.com/DKISTDC/dkist/pull/295>`_)
- Implement missing ``select_tag`` method of ``DatasetConverter``. (`#297 <https://github.com/DKISTDC/dkist/pull/297>`_)
- Update varying celestial transform schema ref to use a uri instead of a tag. (`#298 <https://github.com/DKISTDC/dkist/pull/298>`_)
- Ensure that we don't nest Dask arrays when no FITS files can be read.
  This might result in more memory being used when computing an array with missing files. (`#301 <https://github.com/DKISTDC/dkist/pull/301>`_)


1.0.0 (2023-08-09)
==================

Features
--------

- Add a new `dkist.load_dataset` function to combine and replace ``Dataset.from_directory()`` and ``Dataset.from_asdf()``. (`#274 <https://github.com/DKISTDC/dkist/pull/274>`_)
- Add the ability to load more than one asdf file at once to `dkist.load_dataset`. (`#287 <https://github.com/DKISTDC/dkist/pull/287>`_)


Bug Fixes
---------

- Fix minor bugs for header slicing functionality and expand test coverage for edge-cases. (`#275 <https://github.com/DKISTDC/dkist/pull/275>`_)
- Fixed inverse transform in `.VaryingCelestialTransformSlit2D`. Which fixes a bug in VISP WCSes. (`#285 <https://github.com/DKISTDC/dkist/pull/285>`_)
- Fix a bug preventing the transfer of a single dataset with :meth:`~dkist.net.transfer_complete_datasets`. (`#288 <https://github.com/DKISTDC/dkist/pull/288>`_)


Improved Documentation
----------------------

- Added a new tutorial section based on the NSO workshop material. (`#281 <https://github.com/DKISTDC/dkist/pull/281>`_)


Trivial/Internal Changes
------------------------

- Add jsonschema as an explicit dependency (previously it was provided by asdf). (`#274 <https://github.com/DKISTDC/dkist/pull/274>`_)
- Update minimum required versions of asdf, asdf-astropy, dask, matplotlib, numpy, parfive, and sunpy. (`#275 <https://github.com/DKISTDC/dkist/pull/275>`_)


v1.0.0b15 (2023-07-24)
======================

Features
--------

- Add path interpolation to :meth:`~dkist.net.transfer_complete_datasets` path location argument. (`#266 <https://github.com/DKISTDC/dkist/pull/266>`_)
- Add a `.Dataset.inventory` attribute to more easily access the inventory metadata (previously ``.meta['inventory']``. (`#272 <https://github.com/DKISTDC/dkist/pull/272>`_)
- Add experimental support for 3D LUTs to ``TimeVaryingCelestialTransform`` classes. (`#277 <https://github.com/DKISTDC/dkist/pull/277>`_)


Bug Fixes
---------

- Improve speed of ``import dkist`` by preventing automatic import of ``dkist.net``. (`#266 <https://github.com/DKISTDC/dkist/pull/266>`_)
- Fix how Fido uses Wavelength to search for datasets. (`#266 <https://github.com/DKISTDC/dkist/pull/266>`_)
- Fix using ``a.dkist.Embargoed.false`` and ``a.dkist.Embargoed.true`` to specify embargo status. (`#266 <https://github.com/DKISTDC/dkist/pull/266>`_)
- Add units support to ``a.dkist.FriedParameter``. (`#266 <https://github.com/DKISTDC/dkist/pull/266>`_)
- Add search attrs corresponding to new columns in dataset inventory. (`#266 <https://github.com/DKISTDC/dkist/pull/266>`_)
- Make `dkist.Dataset` return the appropriately sliced header table when slicing data. (`#271 <https://github.com/DKISTDC/dkist/pull/271>`_)
- Update docstring for :meth:`dkist.net.transfer_complete_datasets` to include previously missing ``path`` parameter. (`#273 <https://github.com/DKISTDC/dkist/pull/273>`_)


1.0.0b14 (2023-06-12)
=====================

Features
--------

- Adds support to Ravel for N-dimensional data. (`#249 <https://github.com/DKISTDC/dkist/pull/249>`_)


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

- Drop support for Python 3.8 in line with `NEP 29 <https://numpy.org/neps/nep-0029-deprecation_policy.html>`__. (`#232 <https://github.com/DKISTDC/dkist/pull/232>`_)
- Add new methods :meth:`.FileManager.quality_report` and :meth:`.FileManager.preview_movie` to download the quality report and preview movie. These are accessed as ``Dataset.files.quality_report`` and ``Dataset.files.preview_movie``. (`#235 <https://github.com/DKISTDC/dkist/pull/235>`_)


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
- Fix, and make required, the unit property on a dataset in ASDF files. (`#221 <https://github.com/DKISTDC/dkist/pull/221>`_)


Bug Fixes
---------

- Fix bugs in testing caused by the release of ``pytest 7.2.0``. (`#210 <https://github.com/DKISTDC/dkist/pull/210>`_)
- Make loading a mosaiced VBI dataset work with ``Dataset.from_asdf``. (`#213 <https://github.com/DKISTDC/dkist/pull/213>`_)
- Add support for Python 3.11 (`#218 <https://github.com/DKISTDC/dkist/pull/218>`_)


Improved Documentation
----------------------

- Add documentation for available path interpolation keys. (`#207 <https://github.com/DKISTDC/dkist/pull/207>`_)


1.0.0b9 (2022-09-30)
====================

Features
--------

- Add a ``label=`` kwarg to `.FileManager.download` and `dkist.net.transfer_complete_datasets` allowing the user to completely customise the Globus transfer task label. (`#193 <https://github.com/DKISTDC/dkist/pull/193>`_)


Bug Fixes
---------

- Successfully ask for re-authentication when Globus token is stale. (`#197 <https://github.com/DKISTDC/dkist/pull/197>`_)
- Fix a bug where ``FileManager.download`` would fail if there was not an
  asdf file or quality report PDF in inventory. (`#199 <https://github.com/DKISTDC/dkist/pull/199>`_)
- Fix an issue with slicing a dataset where the slicing wouldn't work correctly
  if the first axis of the data array has length one. (`#199 <https://github.com/DKISTDC/dkist/pull/199>`_)
- No more invalid characters in default Globus label name. (`#200 <https://github.com/DKISTDC/dkist/pull/200>`_)
- Hide extraneous names in `dkist.net.attrs` with underscores so they don't get imported when using that module. (`#201 <https://github.com/DKISTDC/dkist/pull/201>`_)
- Catch empty return value from data search in `dkist.net.transfer_complete_datasets` and raise a ``ValueError`` telling the user what's happening. (`#204 <https://github.com/DKISTDC/dkist/pull/204>`_)


v1.0.0b8 (2022-07-18)
=====================

Features
--------

- Support passing a whole `~sunpy.net.fido_factory.UnifiedResponse` to `~dkist.net.transfer_complete_datasets`. (`#165 <https://github.com/DKISTDC/dkist/pull/165>`_)
- Support pretty formatting of new Dataset Inventory fields in Fido search results table. (`#165 <https://github.com/DKISTDC/dkist/pull/165>`_)


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
  a third pixel axis. (`#148 <https://github.com/DKISTDC/dkist/pull/148>`_)
- Add ASDF serialization for `VaryingCelestialTransform` and `CoupledCompoundModel`. (`#156 <https://github.com/DKISTDC/dkist/pull/156>`_)


Bug Fixes
---------

- Fix asdf using old schema and tag versions when saving new files. (`#157 <https://github.com/DKISTDC/dkist/pull/157>`_)


Trivial/Internal Changes
------------------------

- Migate to the asdf 2.8+ ``Converter`` interface, this bumps various
  dependencies but should have no effect on reading or writing asdf files. (`#152 <https://github.com/DKISTDC/dkist/pull/152>`_)


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
  exists in the new base class and the download method is in the separate child
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

- Implement `.DKISTClient.fetch` to download asdf files from the metadata streamer service. (`#90 <https://github.com/DKISTDC/dkist/pull/90>`_)
- Enable tests on Windows (`#95 <https://github.com/DKISTDC/dkist/pull/95>`_)
- Added search bounding box functionality to DKIST client. (`#100 <https://github.com/DKISTDC/dkist/pull/100>`_)
- Added support for new dataset search parameters (``hasSpectralAxis``, ``hasTemporalAxis``, ``averageDatasetSpectralSamplingMin``, ``averageDatasetSpectralSamplingMax``, ``averageDatasetSpatialSamplingMin``, ``averageDatasetSpatialSamplingMax``, ``averageDatasetTemporalSamplingMin``, ``averageDatasetTemporalSamplingMax``) (`#108 <https://github.com/DKISTDC/dkist/pull/108>`_)


Trivial/Internal Changes
------------------------

- Support gwcs 0.14 and ndcube 2.0.0b1 (`#86 <https://github.com/DKISTDC/dkist/pull/86>`_)
- Update Fido client for changes in sunpy 2.1; bump the sunpy dependency to at least 2.1rc3. (`#89 <https://github.com/DKISTDC/dkist/pull/89>`_)


v0.1a2 (2020-04-29)
===================

Features
--------

- Move asdf generation code into dkist-inventory package (`#79 <https://github.com/DKISTDC/dkist/pull/79>`_)


v0.1a1 (2020-03-27)
===================

Backwards Incompatible Changes
------------------------------

- Move the ``dkist.asdf_maker`` package to ``dkist.io.asdf.generator`` while also refactoring its internal structure to hopefully make it a little easier to follow. (`#71 <https://github.com/DKISTDC/dkist/pull/71>`_)


Features
--------

- Add `dkist.Dataset` class to represent a dataset to the user. (`#1 <https://github.com/DKISTDC/dkist/pull/1>`_)
- Add code for converting a nested list of `asdf.ExternalArrayReference` objects to a `dask.array.Array`. (`#1 <https://github.com/DKISTDC/dkist/pull/1>`_)
- Add implementation of ``Dataset.pixel_to_world`` and ``Dataset.world_to_pixel``. (`#1 <https://github.com/DKISTDC/dkist/pull/1>`_)
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
- Add ``relative_to`` kwarg to ``dkist.asdf_maker.generator.dataset_from_fits`` and ``dkist.asdf_maker.generator.asdf_tree_from_filenames``. (`#26 <https://github.com/DKISTDC/dkist/pull/26>`_)
- Add support for 2D plotting with WCSAxes. (`#27 <https://github.com/DKISTDC/dkist/pull/27>`_)
- All asdf files are now validated against the level 1 dataset schema on save and load. (`#41 <https://github.com/DKISTDC/dkist/pull/41>`_)
- Add support for returning an array of NaNs when the file is not present. This is needed to support partial dataset download from the DC. (`#43 <https://github.com/DKISTDC/dkist/pull/43>`_)
- Add utilities for doing OAuth with Globus. (`#46 <https://github.com/DKISTDC/dkist/pull/46>`_)
- Add helper functions for listing a globus endpoint (`#49 <https://github.com/DKISTDC/dkist/pull/49>`_)
- Add support for multiple globus oauth scopes (`#50 <https://github.com/DKISTDC/dkist/pull/50>`_)
- Added support for starting and monitoring Globus transfer tasks (`#55 <https://github.com/DKISTDC/dkist/pull/55>`_)
- Allow easy access to the filenames contained in an
  ``dkist.io.BaseFITSArrayContainer`` object via a ``.filenames`` property. (`#56 <https://github.com/DKISTDC/dkist/pull/56>`_)
- ``dkist.io.BaseFITSArrayContainer`` objects are now sliceable. (`#56 <https://github.com/DKISTDC/dkist/pull/56>`_)
- Initial implementation of ``dkist.Dataset.download`` method for transferring files via globus (`#57 <https://github.com/DKISTDC/dkist/pull/57>`_)
- Rely on development NDCube 2 for all slicing and plotting code (`#60 <https://github.com/DKISTDC/dkist/pull/60>`_)
- Change Level 1 asdf layout to use a tag and schema for ``Dataset``. This allows
  reading of asdf files independent from the `dkist.Dataset` class. (`#66 <https://github.com/DKISTDC/dkist/pull/66>`_)
- Implement a new more efficient asdf schema and tag for ``BaseFITSArrayContainer`` to massively improve asdf load times. (`#70 <https://github.com/DKISTDC/dkist/pull/70>`_)
- Add a `sunpy.net.Fido` client for searching DKIST Dataset inventory. Currently only supports search. (`#73 <https://github.com/DKISTDC/dkist/pull/73>`_)
- Implement correct extraction of dataset inventory from headers and gwcs. Also
  updates some data to be closer to the in progress outgoing header spec (214) (`#76 <https://github.com/DKISTDC/dkist/pull/76>`_)


Bug Fixes
---------

- Fix the units in ``spatial_model_from_header`` (`#19 <https://github.com/DKISTDC/dkist/pull/19>`_)
- Correctly parse headers when generating gwcses so that only values that change
  along that physical axis are considered. (`#21 <https://github.com/DKISTDC/dkist/pull/21>`_)
- Reverse the ordering of gWCS objects generated by ``asdf_helpers`` as they are
  cartesian ordered not numpy ordered (`#21 <https://github.com/DKISTDC/dkist/pull/21>`_)
- Fix incorrect compound model tree splitting when the split needed to happen at the top layer (`#23 <https://github.com/DKISTDC/dkist/pull/23>`_)
- Fix a lot of bugs in dataset generation and wcs slicing. (`#24 <https://github.com/DKISTDC/dkist/pull/24>`_)
- Fix incorrect chunks when creating a dask array from a loader_array. (`#26 <https://github.com/DKISTDC/dkist/pull/26>`_)
- Add support for dask 2+ and make that the minimum version (`#68 <https://github.com/DKISTDC/dkist/pull/68>`_)


Trivial/Internal Changes
------------------------

- Migrate the `dkist.Dataset` class to use gWCS's APE 14 API (`#32 <https://github.com/DKISTDC/dkist/pull/32>`_)
