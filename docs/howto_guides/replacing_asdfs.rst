.. _dkist:howto-guide:replacing-asdfs:

Replacing Previously Downloaded ASDF Files
==========================================

The DKIST Data Center will occasionally update the ASDF files for all the datasets it stores, due to changes or corrections to the metadata.
This can lead to two possible problems.
First, when you download ASDF metadata files from the Data Center those files might be expecting a newer version of the Python tools.
Second, ASDF files you have downloaded previously might become outdated and need to be re-downloaded.


Re-downloading ASDF files
-------------------------

You should periodically re-download your local ASDF files to keep up to date with changes to the dataset metadata.
To do so, you can use the `overwrite` keyword argument when downloading an ASDF file.
For example, to force a refresh of your local copy of the sample data:

.. code-block:: python

    from dkist.data.sample import download_all_sample_data

    download_all_sample_data(overwrite=True) # doctest: +REMOTE_DATA


`Fido.fetch` also takes the `overwrite` argument.

Occasionally, the naming convention for the ASDF files might also change, meaning that the usual checks to stop you downloading a dataset you already have locally will fail and you will end up with two (likely identical) metadata files.
In this case, if the metadata file has been renamed then you may see a warning like this when you load the dataset:

.. code-block:: python

    >>> from dkist import load_dataset
    >>> ds = load_dataset('~/sunpy/data/VISP/AGLKO/') # doctest: +SKIP

    WARNING: DKISTUserWarning: ASDF files with old names (VISP_L1_20221024T212807_AGLKO_user_tools.asdf) were found in this directory and ignored. You may want to delete these files. [dkist.dataset.loader]


When this happens the newer ASDF file is loaded so the old one can safely be ignored.
However, to remove the warning the old file can simply be deleted or moved elsewhere.

Note that this behaviour is new in dkist v1.10.0.
In older versions the loader will return a list containing the corresponding dataset for each ASDF file present, which is likely to cause problems.
Deleting the old file will still solve the issue, although you should also update your Python tools installation to v1.10.1 or later if possible.

Understanding version warnings when loading ASDFs
-------------------------------------------------

When you load a recently-downloaded ASDF file you may see a warning something like this:

::

    AsdfPackageVersionWarning: File '<file you tried to load>' was created with extension URI 'asdf://asdf-format.org/astronomy/gwcs/extensions/gwcs-1.2.0' (from package gwcs==0.24.0), but older package (gwcs==0.22.0) is installed.


Of course the extension and package it complains about will vary.
This warning means that an extension needed to properly parse the ASDF file is missing or outdated.
To correct this, you should update your Python tools installation with

.. code-block:: bash

    pip install --upgrade dkist


if you installed using `pip` or

.. code-block:: bash

    conda update dkist


if you used `conda`.
