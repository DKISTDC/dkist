.. _dkist:howto-guide:replacing-asdfs:

Replacing Previously Downloaded ASDF Files
==========================================

The DKIST Data Center will occasionally update the ASDF files for all the datasets it stores, due to changes or corrections to the metadata.
When this happens, you may see a warning message when opening ASDF files locally after updating your Python tools installation.
To remove the warning you will need to update your local ASDF files as described below.


Replacing Sample Data
---------------------

The sample datasets included with the Python tools will occasionally be updated with a new release of the package.
When this happens you may see the following warning (or something similar) when you try to load sample data:

.. code-block:: python

    >>> from dkist.data.sample import VBI_AJQWW # doctest: +REMOTE_DATA
    >>> from dkist import load_dataset
    >>> ds = load_dataset(VBI_AJQWW) # doctest: +REMOTE_DATA

    asdf.exceptions.AsdfPackageVersionWarning: File 'file:///home/runner/.local/share/dkist/VBI_AJQWW/VBI_L1_20231016T184519_AJQWW_metadata.asdf' was created with extension URI 'asdf://astropy.org/core/extensions/core-1.5.0' (from package asdf-astropy==0.5.0), which is not currently installed


To update the local files, you can use the utility function in `dkist.data.sample` to re-download them and force it to replace them using the `overwrite` keyword arg.


.. code-block:: python

    from dkist.data.sample import download_all_sample_data

    download_all_sample_data(overwrite=True) # doctest: +REMOTE_DATA


In this specific instance you will also want to update `asdf-astropy` to v0.7.1 or later, but replacing the ASDF files will also solve any other problems caused by outdated sample data.

Replacing Other Data
--------------------

There are two cases in which metadata files for other datasets might have to be replaced.
First, the metadata itself or the internal structure of the files may have been updated but the name kept the same.
Second, the naming convention for the ASDF files might occasionally change, meaning that the usual checks to stop you downloading a dataset you already have locally will fail and you will end up with two (likely identical) metadata files.

In the case where the Data Center's copy of the metadata file has been updated but not renamed, the normal download process will not automatically download the updated file:

.. code-block:: python

    from sunpy.net import Fido, attrs as a
    import dkist.net

    # Search for some dataset we already have locally
    res = Fido.search(a.dkist.Dataset('AGLKO')) # doctest: +REMOTE_DATA

    # Download the asdf file
    f = Fido.fetch(res, path="~/sunpy/data/{instrument}/{dataset_id}") # doctest: +REMOTE_DATA


To force Fido to download the new file, we can use the overwrite keyword argument again:

.. code-block:: python

    f = Fido.fetch(res, path="~/sunpy/data/{instrument}/{dataset_id}", overwrite=True) # doctest: +REMOTE_DATA


In the second case, if the metadata file has been renamed then you may see a warning like this when you load the dataset:

.. code-block:: python

    >>> from dkist import load_dataset
    >>> ds = load_dataset('~/sunpy/data/VISP/AGLKO/') # doctest: +REMOTE_DATA

    WARNING: DKISTUserWarning: ASDF files with old names (VISP_L1_20221024T212807_AGLKO_user_tools.asdf) were found in this directory and ignored. You may want to delete these files. [dkist.dataset.loader]


When this happens the newer ASDF file is loaded so the old one can safely be ignored.
However, to remove the warning the old file can simply be deleted or moved elsewhere.

Note that this behaviour is new in dkist v1.10.0.
In older versions the loader will return a list containing the corresponding dataset for each ASDF file present, which is likely to cause problems.
Deleting the old file will still solve the issue, although you should also update your Python tools installation to v1.10.1 or later if possible.
