.. _dkist-dataset:

Dataset Module
==============

The `~dkist.dataset.Dataset` class is provided as a loader for a whole DKIST
dataset. Given a directory containing a number of FITS files and the dataset
asdf file, the dataset will be loaded into an array.


Components of a Dataset
-----------------------

A DKIST dataset is comprised of one observation from one instrument at a given
time. The `~dkist.dataset.Dataset` can be thought of as a coordinate aware
array, it has a very similar interface to the :ref:`SunPy ndcube <ndcube>` package.


The `~dkist.dataset.Dataset` object consists of two primary components a `Dask
Array <http://dask.pydata.org/en/latest/array.html>`__ object which will read
the data from the FITS file which comprise a dataset on demand, and a `gWCS
<https://gwcs.readthedocs.io/en/latest/>`__ (Generalised World Coordinate
System) object which can convert between pixel and world coordinates.


Constructing a Dataset
----------------------

A dataset should be constructed from a directory, containing one asdf file and a
set of FITS files. All the metadata is read from the asdf file, and only the
arrays are read from the FITS file.::


  >>> from dkist.dataset import Dataset
  >>> ds = Dataset.from_directory("/my/directory") # doctest: +SKIP


Slicing a Dataset
-----------------


Plotting a Dataset
------------------



API Documenation
----------------

.. automodapi:: dkist.dataset
   :headings: ^#
