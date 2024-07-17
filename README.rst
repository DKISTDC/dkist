DKIST User Tools
================

.. image:: https://img.shields.io/pypi/v/dkist.svg
   :target: https://pypi.python.org/pypi/dkist/
   :alt: PyPI for dkist package
.. image:: https://img.shields.io/pypi/pyversions/dkist
   :alt: PyPI - Python Version
.. image:: https://img.shields.io/matrix/dki-solar-telescope:openastronomy.org.svg?colorB=%23FE7900&label=Chat&logo=matrix&server_fqdn=matrix.org
   :target: https://app.element.io/#/room/#dki-solar-telescope:openastronomy.org
   :alt: DKIST chat room on matrix
.. image:: https://github.com/DKISTDC/dkist/actions/workflows/main.yml/badge.svg?branch=main
   :target: https://github.com/DKISTDC/dkist/actions/workflows/main.yml
   :alt: Latest CI Status for dkist package
.. image:: https://codecov.io/github/dkistdc/dkist/branch/master/graph/badge.svg?token=A4ggaCurqz
   :target: https://codecov.io/github/dkistdc/dkist
   :alt: Latest codecov Status for dkist package
.. image:: https://readthedocs.com/projects/dkistdc-dkist/badge/?version=latest
   :target: https://docs.dkist.nso.edu/projects/python-tools
   :alt: Documentation Status
.. image:: http://img.shields.io/badge/powered%20by-SunPy-orange.svg?style=flat
   :target: http://www.sunpy.org
   :alt: Powered by SunPy Badge

A Python library of tools for obtaining, processing and interacting with DKIST
data.

Documentation
-------------

See the documentation at `https://docs.dkist.nso.edu/projects/python-tools <https://docs.dkist.nso.edu/projects/python-tools>`__.

Installation
------------

The recommended way to install ``dkist`` is with `miniforge <https://github.com/conda-forge/miniforge#miniforge3>`__.
To install ``dkist`` once miniforge is installed run the following command:

.. code:: bash

    $ conda install dkist

For detailed installation instructions, see the `installation guide <https://docs.dkist.nso.edu/projects/python-tools/en/stable/installation.html>`__ in the ``dkist`` docs.

License
-------

This project is Copyright (c) NSO / AURA and licensed under
the terms of the BSD 3-Clause license.

Code of Conduct
---------------

When you are interacting with the `dkist` project you are asked to follow the SunPy `Code of Conduct <https://sunpy.org/coc>`__.

Releasing The `dkist` package
-----------------------------

Doing a release of this package is automated using GitHub actions, the release can be done following these steps:

1. Run the pre-release workflow on GitHub actions, this can be done by clicking "run workflow" `here <https://github.com/DKISTDC/dkist/actions/workflows/prepare-release.yml>`__.
2. That workflow will have opened a PR, you should review it and merge it as normal.
3. That workflow will also have drafted a GitHub release `here <https://github.com/DKISTDC/dkist/releases>`__, once the PR is merged you can publish that release, this will trigger the rest as long as the CI passes.
