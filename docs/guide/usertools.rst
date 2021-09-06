.. _usertools:

What to Expect from the DKIST Python Tools
==========================================

The `dkist` package is developed by the DKIST Data Center team, and it is designed to make it easy to obtain and use DKIST data in Python.
To achieve this goal the `dkist` package only provides DKIST specific functionality as plugins and extensions to the wider `sunpy` and scientific Python ecosystem.
This means that there *isn't actually a lot of code* in the `dkist` package, and most of the development effort required to support DKIST data happened in packages such as `ndcube`, `sunpy` and `astropy`.

The upshot of this when using the DKIST Python tools is that you will mostly not be (directly) using functionality provided by the `dkist` package.
You will need to be familiar with the other packages in the ecosystem to make use of the tools provided here.
The main things you will need to know are the `sunpy.net.Fido` and `ndcube.NDCube` classes.


Technical Details
-----------------

What the `dkist` package provides is the following:

* A subclass of `ndcube.NDCube` which hooks into our ASDF schemas and provides access to the table of FITS headers and the `dkist.io.FileManager` object.
* A client class for `sunpy.net.Fido` which transparently loads on import of `dkist.net` and allows Fido to search the DKIST data center.
* A set of helper functions to transfer files from the data center via `Globus <https://globus.org/>`__, the way to call this is the `~dkist.io.FileManager.download` of the `dkist.Dataset.files` property.

This facilitates search, retrieval and loading of level 1 data using the functionality provided by `sunpy` and `ndcube`.
It is expected that any community developed analysis software that is explicitly DKIST specific will also be included in the `dkist` package in the future.
