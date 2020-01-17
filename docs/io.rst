IO Module
=========

This module handles building a single Python array from a collection of FITS files.

The data that this module is built to work with is an array of
`asdf.ExternalArrayReference` objects. This is an array of arrays, for which we
expose a single Python array-like object. This is done by instantiating a
`dkist.io.loaders.BaseFITSLoader` object for each `asdf.ExternalArrayReference`
object, these loader objects, provide a delayed-io interface to the FITS file,
only opening the file for reading when the data or the header is accessed.

The `~dkist.io.array_containers.BaseFITSArrayContainer` class handles
converting an array of `asdf.ExternalArrayReference` objects into an array of
`~dkist.io.loaders.BaseFITSLoader` objects and then providing a method of
converting this array of loaders into an array class. Currently, a container for
`numpy.ndarray` and `dask.array.Array` are provided.

API Reference
-------------

.. automodapi:: dkist.io.loaders
   :headings: #^

.. automodapi:: dkist.io.array_containers
   :headings: #^

.. automodapi:: dkist.io.asdf.generator
   :headings: #^
