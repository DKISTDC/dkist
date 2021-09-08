.. _loadinglevel1data:

Loading and Working with Level One Data
=======================================

As we saw in the :ref:`downloading-fits` section, once we have an ASDF file representing a DKIST dataset it can be loaded with `dkist.Dataset`.
The `dkist.Dataset` class provides access to all the components of the dataset, and is a slightly customised `ndcube.NDCube` object, so all functionality provided by ndcube is applicable to the ``Dataset`` class.

This section of the guide will cover the basics of using the `~dkist.Dataset` class, but will not dive into the details which are covered by the `ndcube documentation <https://docs.sunpy.org/projects/ndcube>`__.
In particular we recommend you read the following sections of the ``ndcube`` documentation:

* :ref:`ndcube:ndcube`
* :ref:`ndcube:coordinates`
* :ref:`ndcube:slicing`

before coming back to this guide.

The Components of a `~dkist.Dataset`
------------------------------------

Before we dive in, let us look at the core components of the `~dkist.Dataset` object and what each of them provides.
All of these components are available when an ASDF file is loaded, even if no FITS files have been downloaded, however, no data will be available without the FITS files (all pixels will be NaN).

* The `~dkist.Dataset.data` property is a `dask.array.Array` object which lazy loads the array data from the FITS files on demand.
* The `~dkist.Dataset.wcs` property is a `gwcs.wcs.WCS` object which provides coordinate information for all the pixels in the array.
* The `~dkist.Dataset.files` property is an instance of the `dkist.io.FileManager` class which allows you to access and modify information about how the FITS files are loaded by the array.
* The `~dkist.Dataset.headers` property is an `astropy.table.QTable` instance which is a complete record of all the FITS headers for all the FITS files in the dataset. This provides access to all the available metadata about the dataset without having to retrieve or open any of the FITS files.

The relationship between `~dkist.Dataset.data` and `~dkist.Dataset.files`
#########################################################################

When an ASDF file containing a dataset is loaded, a new array is generated from the list of FITS filenames provided in that ASDF file.
These FITS filenames are ordered in the correct way so that an array of the correct dimensionality to represent the whole dataset as a higher dimensional array that is contained in any FITS file.
Depending on how the ASDF file was obtained, you may or may not have some or all of the corresponding FITS files.
If any of the FITS files referenced by the ADSF file are in the same directory as the ASDF file they will be opened automatically when their slice of the array is requested.

The `~dkist.io.FileManager` object is provided to let you inspect and modify how this loading occurs.
The two main functions it enables are: modifying the base path for where the FITS files are loaded from, and transferring FITS files using Globus.
The `~dkist.io.FileManager.basepath` property sets the directory from which the FITS files will be loaded on demand; assigning this to a different directory will cause the FITS to be loaded from that path.
If at any point the file with the required filename as specified by the ASDF can not be found its slice of the array will be returned as NaN.
The `~dkist.io.FileManager.download` method is designed to allow you to transfer some or all of the FITS files from the data center using Globus.
For more details on how to use it see the :ref:`downloading-fits` section.
It is important to note that `~dkist.io.FileManager.download` will set the `~dkist.io.FileManager.basepath` property to the destination directory when using a local personal endpoint.
