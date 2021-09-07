.. _searchdownload:

Searching and Downloading Level One Data
========================================

The DKIST Data Center provides a search interface for searching all level 1 datasets and makes ASDF files available to download over HTTP, while FITS files are transferred via Globus.
The DKIST Python tools makes use of sunpy's pluggable search and download API, which is described in :ref:`sunpy:fido_guide`.

.. note::

   Download of FITS files is not provided through the ``Fido`` interface.
   As is described below, FITS files can be downloaded for some or all of a dataset after reading the ASDF file.


Searching for DKIST Data with Fido
----------------------------------

As is descibed in :ref:`sunpy:fido_guide`, searches through ``Fido`` use "attrs" which specify the search criteria.
A single search can match one or more data providers, for example it is possible to search for DKIST data and data provided by the VSO simultaneously.
In this guide we will focus on searches only for DKIST data through using the client provided in `dkist.net`.

In addition to the core set of "attrs" provided by `sunpy.net.attrs` most of which can be used, there is also a set of attrs specific to the `dkist.net` client, which are listed here: `dkist.net.attrs`.

An example search is:

.. code-block:: python

   from sunpy.net import Fido, attrs as a
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
