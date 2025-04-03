.. _dkist:howto-guide:replacing-asdfs:

Update Previously Downloaded ASDF Files
=======================================

The DKIST Data Center will occasionally update the ASDF files for all the datasets it stores, due to changes or corrections to the metadata.
This means that ASDF files you have downloaded previously might become outdated and need to be re-downloaded.

You should periodically re-download your local ASDF files to keep up to date with changes to the dataset metadata.
To do so, you can use the `overwrite` keyword argument when downloading an ASDF file.

For example:

.. code-block:: python

    Fido.fetch(res, path="~/sunpy/data/{instrument}/{dataset_id}", overwrite=True) # doctest: +SKIP


where ``res`` is the result of a ``Fido`` search for some dataset you already have saved locally.

You might also need to force a refresh of the sample data which is included with the Python tools.
Again, we can use the ``overwrite`` keyword for this.

.. code-block:: python

    from dkist.data.sample import download_all_sample_data

    download_all_sample_data(overwrite=True) # doctest: +REMOTE_DATA


In the past, the naming convention for the metadata ASDF files has also changed, meaning that the usual checks to stop you downloading a dataset you already have locally may fail and you will end up with two separate metadata files.
If you try and load a dataset where a file with an old name is present you will see a warning similar to this:

.. code-block:: python

    >>> from dkist import load_dataset
    >>> ds = load_dataset('~/sunpy/data/VISP/AGLKO/') # doctest: +SKIP

    WARNING: DKISTUserWarning: ASDF files with old names (VISP_L1_20221024T212807_AGLKO_user_tools.asdf) were found in this directory and ignored. You may want to delete these files. [dkist.dataset.loader]


When this happens the newer ASDF file is loaded so the old one can safely be ignored.
However, to remove the warning the old file can simply be deleted or moved elsewhere.

Note that this warning was added in dkist version 1.10.0.
In older versions the loader will return a list containing the corresponding dataset for each ASDF file present, which is likely to cause problems.
Deleting the old file will still solve the issue, although you should also update your Python tools installation to v1.10.0 or later.
