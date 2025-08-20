.. NOTE THE URL FOR THIS PAGE IS IN THE EXCEPTION RAISED IN LOAD_DATASET
.. If you rename this file you will need to update that URL

.. _dkist:howto-guide:asdf-dkist-version:

Understand version requirements for ASDF Files
==============================================

The ASDF files provided by the DKIST Data Center (and other ASDF files) use plugins provided by various Python libraries to load Python objects such as `dkist.Dataset` and `gwcs.WCS`.
For this reason, it's ill advised to load a DKIST ASDF file with a version of the `dkist` package older than the one used to create it.

By default, starting with `dkist` version 1.14 an error will be raised in `dkist.laod_dataset` when attempting to read an ASDF file with a version of `dkist` older than the one used to write it.

You may also see warnings something like this:

::

    AsdfPackageVersionWarning: File '<file you tried to load>' was created with extension URI 'asdf://asdf-format.org/astronomy/gwcs/extensions/gwcs-1.2.0' (from package gwcs==0.24.0), but older package (gwcs==0.22.0) is installed.


The extension and package it references will vary.

These errors and warnings mean that the `dkist` package or one of its dependencies is out of date.


Updating `dkist` and it's dependencies
--------------------------------------

To update `dkist` and any required dependencies, you should update your Python tools installation with

.. code-block:: bash

    pip install --upgrade dkist


if you installed using `pip` or

.. code-block:: bash

    conda update dkist


if you used `conda`.

.. warning::

   If your version of Python is no longer supported by `dkist` you will only get older versions of `dkist` when upgrading and the error will not go away. In this case you need to create a new Python environment with a newer version of Python.

   `dkist` follows the community standard support lifetimes for Python as detailed in `SPEC 0 <https://scientific-python.org/specs/spec-0000/>`__.


Why do you require me to upgrade `dkist`?
-----------------------------------------

The DKIST data center creates the metadata ASDF files with the minimum versions of `dkist` and its dependencies possible.
However, there are some times when changes to the ASDF file require the latest version of `dkist` for new instrument support, major performance improvements or other urgent fixes.
We expect these events to become more infrequent as the observatory and the data products mature over the coming years.
