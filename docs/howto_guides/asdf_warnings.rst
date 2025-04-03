.. _dkist:howto-guide:asdf-warnings:

Understand version warnings when loading ASDFs
==============================================

When you load a recently-downloaded ASDF file you may see a warning something like this:

::

    AsdfPackageVersionWarning: File '<file you tried to load>' was created with extension URI 'asdf://asdf-format.org/astronomy/gwcs/extensions/gwcs-1.2.0' (from package gwcs==0.24.0), but older package (gwcs==0.22.0) is installed.


The extension and package it references will vary.
This warning means that the `dkist` package or one of its dependencies is out of date.
To correct this, you should update your Python tools installation (and its dependencies) with

.. code-block:: bash

    pip install --upgrade dkist


if you installed using `pip` or

.. code-block:: bash

    conda update dkist


if you used `conda`.
