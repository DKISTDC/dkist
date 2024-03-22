.. _dkist:topic-guides:searchdownload:

Searching and Downloading Level One Data
========================================

The DKIST Data Center provides a search interface for searching for level one datasets.
This means you can search for whole collections of FITS files, each with an associated ASDF metadata file and other ancillary files (such as preview movies).
The ASDF and other ancillary files are made available to download over HTTP, to transfer the FITS files we use `Globus <https://www.globus.org/data-transfer>`__.

.. _dkist:topic-guides:searching-datasets:

Searching for DKIST Datasets with Fido
--------------------------------------

.. note::

   Download of FITS files is not provided through the ``Fido`` interface.
   As is described below, FITS files can be downloaded for some or all of a dataset after reading the ASDF file.

As is described in :ref:`sunpy:sunpy-tutorial-acquiring-data-index`, searches through ``Fido`` use "attrs" which specify the search criteria.
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

.. _dkist:topic-guides:downloading-asdf:

Downloading the ASDF Metadata Files
###################################

Once you have identified one or more datasets of interest, you can download the metadata only ASDF file using ``Fido.fetch``.

.. code-block:: python

   files = Fido.fetch(results)

This will return a list-like object which contains one or more filepaths to the downloaded ASDF files.

.. _dkist:topic-guides:downloading-fits:

Downloading FITS files with Globus
----------------------------------

As mentioned at the top of the page the DKIST level one data are only available to download using the `Globus <https://www.globus.org/data-transfer>`__ file transfer system.
The `dkist` package provides helpers to orchestrate the transfer of files with Globus.
The objective of these helpers is to provide the tools needed to quickly access some or all of a dataset, and to script the transfer of any data.

The `dkist` package provides two different interfaces for starting a Globus transfer.
One is `~dkist.net.transfer_complete_datasets` which will stage the whole dataset directory for download.
The other is the `~dkist.io.FileManager.download` method of ``Dataset.files``, this method allows you to only download some FITS files based on the slicing of a dataset object.


Downloading Files from a ``Dataset``
####################################

The most flexible way to download FITS files is to first load the dataset into a `~dkist.Dataset` object from an ASDF file.
This workflow enables you to choose what FITS files you want to transfer based on the metadata of the dataset (for example, the wavelength or stokes profile).

The first step in this workflow is to construct a `dkist.Dataset` object from an already downloaded ASDF.

How to do this is detailed in the next section, :ref:`dkist:topic-guides:loadinglevel1data`, but a quick example, following on from the ``Fido.fetch`` call above:

.. code-block:: python

   ds = dkist.load_dataset(files[0])

Once the dataset is loaded, we can use the `dkist.Dataset.files` property to manage where the dataset looks for the FITS files associated with the dataset.
By default the ``Dataset`` object will assume the FITS files are in the same directory as the ASDF file that was loaded.
You can see what this directory is by using the ``ds.files.basepath`` property.

.. code-block:: python

   ds.files.basepath

If you wish to re-point the dataset to look for the FITS files in another directory you can explicitly set this property.
For example:

.. code-block:: python

   ds.files.basepath = "~/data/dkist/BCDEF"

.. note::

   To transfer files to your local computer you will need a running instance of the `Globus Connect Personal (GCP) <https://www.globus.org/globus-connect-personal>`__ software.
   All the following documentation assumes you have this running and wish to transfer files using GCP to the machine where your Python session is running.
   It is possible to use the `dkist` package to orchestrate transfers to remote endpoints or other more complex arrangements by specifying the ``destination_endpoint=`` keyword argument to all these functions.

Once we have loaded the dataset, if we wish to transfer all the FITS files a single call to `~dkist.io.FileManager.download` will initiate the transfer:

.. code-block:: python

   ds.files.download()

If this is the first time you have run this method, or your authentication has expired, a login page should open in your webbrowser to authenticate with the Globus system.
By default this call will download all the FITS files to the current value of ``ds.files.basepath``, i.e. by default in the same directory as the loaded ASDF file.
You can override this behaviour by using the ``path=`` keyword argument.
The path argument can contain keys which will be replaced by the corresponding values in the dataset's metadata.
For example, setting `path="~/data/dkist/{instrument}/"` will download all files and save them in separate folders named for the instrument.
A full list of the available keys can be found in :ref:`dkist:topic-guides:interpolation-keys`.

The real power of using ``download()`` however, is that you don't have to transfer the FITS files for the frames you do not wish to study (yet).
For instance, imagine the situation where you wish to first inspect the Stokes I profile to asses the viability of the data for your analysis, using this download method you can do this and your transfer will take about a quarter of the time.
The `~dkist.Dataset` class allows you to do this by slicing it, more details of how to do this are described in :ref:`dkist:topic-guides:dataset-slicing`.

Continuing our example of only wanting to download the Stokes I profile we can do this by slicing the 0th element of the first array dimension (the stokes axis):

.. code-block:: python

   ds_I = ds[0]

Then we call download on this new smaller cube:

.. code-block:: python

   ds_I.download()

This will then only transfer the Stokes I frames.


Downloading Complete Datasets
#############################

The alternative way of orchestrating transfers with Globus provided by the `dkist` package is the `dkist.net.transfer_complete_datasets` function.
This will transfer the whole dataset based on a ``Fido`` search result, or the dataset ID.

Given our ``Fido`` search result from earlier:

.. code-block:: python

   from sunpy.net import Fido, attrs as a
   import dkist
   import dkist.net

   results = Fido.search(a.Instrument("VBI"), a.Time("2022-01-01", "2022-01-02"))
   results

If we wanted to transfer all of the datasets returned by this search we could pass the results object to `~.transfer_complete_datasets`:

.. code-block:: python

    transfer_complete_datasets(results["dkist"])

Note how we have to extract the ``"dkist"`` table from the `~sunpy.net.fido_factory.UnifiedResponse` object, as `.transfer_complete_datasets` only operates on DKIST datasets.
This will iterate over each dataset in the results and transfer them one-by-one showing a progress bar for each one.

We could also just transfer a single dataset by slicing the results down to one (or more) rows:

.. code-block:: python

    transfer_complete_datasets(results["dkist"][0])

This would only transfer the first result of the search.

Finally, if you know the dataset ID of a dataset you wish to download, you can just request that dataset be transferred:

.. code-block:: python

    transfer_complete_datasets("AAAAA")

.. _dkist:topic-guides:interpolation-keys:

Path interpolation keys
-----------------------

When downloading DKIST data with ``ds.files.download()`` or ``Fido.fetch(), the ``path=`` keyword argument can be used to specify the target folder for the download.
This path can include keys corresponding to metadata entries, and those values are then used to complete the download path.
For example, to download a dataset into its own folder named with the dataset ID, with separate subfolders for each instrument in the dataset, you could set ``path="~/data/dkist/{dataset_id}/{instrument}/"``.
This would take the values for the dataset ID and instrument name from either the ASDF file or the search results.

Here is a full list of the metadata keywords available for this purpose and their corresponding path interpolation keys:

.. generate:: html

    from dkist.utils.inventory import _path_format_table
    print(_path_format_table())

The complete list of keys can be accessed on the return value from a ``Fido`` search as follows::

  >>> from sunpy.net import Fido, attrs as a
  >>> import dkist.net
  >>> res = Fido.search(a.dkist.Dataset("AGLKO"))  # doctest: +SKIP
  >>> res.path_format_keys()  # doctest: +SKIP
