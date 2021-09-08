.. _searchdownload:

Searching and Downloading Level One Data
========================================

The DKIST Data Center provides a search interface for searching all level 1 datasets and makes ASDF files available to download over HTTP, while FITS files are transferred via Globus.
The DKIST Python tools makes use of sunpy's pluggable search and download API, which is described in :ref:`sunpy:fido_guide`.

.. note::

   Download of FITS files is not provided through the ``Fido`` interface.
   As is described below, FITS files can be downloaded for some or all of a dataset after reading the ASDF file.

.. _searching-datasets:

Searching for DKIST Data with Fido
----------------------------------

As is descibed in :ref:`sunpy:fido_guide`, searches through ``Fido`` use "attrs" which specify the search criteria.
A single search can match one or more data providers, for example it is possible to search for DKIST data and data provided by the VSO simultaneously.
In this guide we will focus on searches only for DKIST data through using the client provided in `dkist.net`.

.. note::

   Remember to import `dkist.net` (not just `dkist`) in any script where using Fido, as importing `dkist.net` registers the DKIST client with Fido.

In addition to the core set of "attrs" provided by `sunpy.net.attrs` most of which can be used, there is also a set of attrs specific to the `dkist.net` client, which are listed here: `dkist.net.attrs`.

An example search is:

.. code-block:: python

   from sunpy.net import Fido, attrs as a
   import dkist
   import dkist.net

   results = Fido.search(a.Instrument("VBI"), a.Time("2022-01-01", "2022-01-02"))
   results

This search would match any datasets taken by the VBI instrument on the 1st January 2022.

It is possible to add as many conditions as needed separated by commas or the ``&`` (and) operator to make your search more restrictive.
It is also possible to use the ``|`` (or) operator to specify multiple criteria, for example:

.. code-block:: python

   results = Fido.search(a.Time("2022-01-01", "2022-01-02"),
                         a.Instrument("VBI") | a.Instrument("VISP"))
   results

This would return any datasets taken by the VBI or VISP instruments in our time range.

Many other combinations of searches are available, such as searching for a specific proposal identifier with `~dkist.net.attrs.Proposal`.

.. _downloading-asdf:

Downloading the ASDF Metadata Files
-----------------------------------

Once you have identified one or more datasets of interest, you can download the metadata only ASDF file using ``Fido.fetch``.

.. code-block:: python

   files = Fido.fetch(results)

This will return a list-like object which contains one or more filepaths to the downloaded ASDF files.

.. _downloading-fits:

Downloading FITS files with Globus
----------------------------------

As is detailed in the next section :ref:`loadinglevel1data` these can be passed to `dkist.Dataset` to open the file.
For example, to load only the first ASDF file we would do:

.. code-block:: python

   ds = dkist.Dataset.from_asdf(files[0])

Once we have loaded the dataset, if we wish to transfer all the FITS files a single call to `~dkist.io.FileManager.download` will initiate the transfer:

.. code-block:: python

   ds.files.download()

If this is the first time you have run this method a login page should open in your webbrowser to authenticate with the Globus system.
Without overriding any of the default arguments calling this method **expects you to already have a running Globus personal endpoint** local to the Python session.
If you wish to transfer the dataset to a non-local endpoint, you can do so by setting the ``destination_endpoint=`` keyword argument.
