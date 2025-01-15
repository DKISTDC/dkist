.. _dkist:howto-guide:sample-data:

Downloading the Sample Data with Globus
=======================================

The Python tools provide a few different partial datasets as sample data, these are used in documentation and examples.
This how to guide will show you how to download the complete data for these datasets, or let you change the dataset for a different one.


Searching for and downloading the ASDF file
-------------------------------------------

Using the `BKPLX <https://dkist.data.nso.edu/datasetview/BKPLX>`__ dataset from the VISP we download the ASDF file and create a `dkist.Dataset` object.

.. code-block:: python

    from sunpy.net import Fido, attrs as a

    import dkist
    import dkist.net

    results = Fido.search(a.dkist.Dataset("BKPLX"))
    asdf_file = Fido.fetch(results)

    ds = dkist.load_dataset(asdf_file)


Downloading the FITS files with Globus
--------------------------------------

Having loaded the ASDF file into a `dkist.Dataset` as this is a VISP dataset with polarimetry, we can download the Stokes I profile by indexing the first element of the first dimension:

.. code-block:: python

    ds[0].files.download()  # doctest: +SKIP

This will download the Stokes I FITS files into the same directory as the ASDF file.

To download the whole dataset do:

.. code-block:: python

    ds.files.download()  # doctest: +SKIP
