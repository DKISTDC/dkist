.. _usertools:

What to Expect from the DKIST Python Tools
==========================================

The `dkist` package is developed by the DKIST Data Center team, and it is designed to make it easy to obtain and use DKIST data in Python.
To achieve this goal the `dkist` package only provides DKIST specific functionality as plugins and extensions to the wider `sunpy` and scientific Python ecosystem.
This means that there *isn't actually a lot of code* in the `dkist` package, and most of the development effort required to support DKIST data happened in packages such as `ndcube`, `sunpy` and `astropy`.
What the `dkist` package provides is the following:

* A subclass of `ndcube.NDCube` which hooks into our ASDF schemas and provides access to the table of FITS headers and the `dkist.io.FileManager` object.
* A client class for `sunpy.net.Fido` which transparently loads on import of `dkist.net` and allows Fido to search the DKIST data center.
* A set of helper functions to transfer files from the data center via `Globus <https://globus.org/>`__, the way to call this is `dkist.Dataset.files.download`.
