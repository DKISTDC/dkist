.. _dkist:developer-guide:index:

Developer Guide
===============

ASDF Files
----------

The way the code in this repo interacts with the way people load and the data centre generates ASDF files is pretty complex.
The DKIST ASDF files are reliant on ADSF plugins from astropy, sunpy, gwcs, and our own in this package.

A DKIST ASDF file has a tree which looks like this::

    root (AsdfObject)
    ├─asdf_library (Software)
    │ ├─author (str): The ASDF Developers
    │ ├─homepage (str): http://github.com/asdf-format/asdf
    │ ├─name (str): asdf
    │ └─version (str): 2.8.4.dev42+gef95881
    ├─history (dict)
    │ └─extensions (list)
    │   ├─[0] (ExtensionMetadata)
    │   │ ├─extension_class (str): asdf.extension._manifest.ManifestExtension
    │   │ ├─extension_uri (str): asdf://asdf-format.org/core/extensions/core-1.5.0
    │   │ └─software (Software)
    │   │   ├─name (str): asdf-astropy
    │   │   └─version (str): 0.1.2
    │   ├─[1] (ExtensionMetadata)
    │   │ ├─extension_class (str): asdf.extension._manifest.ManifestExtension
    │   │ ├─extension_uri (str): asdf://dkist.nso.edu/dkist/extensions/dkist-1.0.0
    │   │ └─software (Software)
    │   │   ├─name (str): dkist
    │   │   └─version (str): 1.0.0b4.dev6+g76680d3.d20220201
    │   ├─[2] (ExtensionMetadata)
    │   │ ├─extension_class (str): asdf.extension._manifest.ManifestExtension
    │   │ ├─extension_uri (str): asdf://asdf-format.org/astronomy/gwcs/extensions/gwcs-1.0.0
    │   │ └─software (Software)
    │   │   ├─name (str): gwcs
    │   │   └─version (str): 0.18.0
    │   ├─[3] (ExtensionMetadata)
    │   │ ├─extension_class (str): asdf.extension._manifest.ManifestExtension
    │   │ ├─extension_uri (str): asdf://asdf-format.org/astronomy/coordinates/extensions/coordinates-1.0.0
    │   │ └─software (Software)
    │   │   ├─name (str): asdf-astropy
    │   │   └─version (str): 0.1.2
    │   ├─[4] (ExtensionMetadata)
    │   │ ├─extension_class (str): asdf.extension.BuiltinExtension
    │   │ └─software (Software)
    │   │   ├─name (str): asdf
    │   │   └─version (str): 2.8.4.dev42+gef95881
    │   ├─[5] (ExtensionMetadata)
    │   │ ├─extension_class (str): asdf.extension._manifest.ManifestExtension
    │   │ ├─extension_uri (str): asdf://astropy.org/astropy/extensions/astropy-1.0.0
    │   │ └─software (Software)
    │   │   ├─name (str): asdf-astropy
    │   │   └─version (str): 0.1.2
    │   ├─[6] (ExtensionMetadata)
    │   │ ├─extension_class (str): asdf.extension._manifest.ManifestExtension
    │   │ ├─extension_uri (str): asdf://asdf-format.org/transform/extensions/transform-1.5.0
    │   │ └─software (Software)
    │   │   ├─name (str): asdf-astropy
    │   │   └─version (str): 0.1.2
    │   └─[7] (ExtensionMetadata)
    │     ├─extension_class (str): sunpy.io.special.asdf.extension.SunpyExtension
    │     └─software (Software)
    │       ├─name (str): sunpy
    │       └─version (str): 3.1.2
    └─dataset (Dataset)

As you can see, there are a number of extensions in use, and one key in the tree ``'dataset'``, which is of type `dkist.Dataset` or `dkist.TiledDataset`.

Various components of the DKIST ASDF extension are versioned.
These are:

* The extension itself via its manifest.
* The ``dataset`` and ``tiled_dataset`` schemas.
* The ``dataset`` and ``tiled_dataset`` tags.
* The ``file_manager`` schema and tag which is referenced by ``dataset``.

Documentation
-------------

Narrative style
***************

All narrative documentation (not docstrings) should be formatted as one sentence per line.
All documentation should be written in US English.

Sphinx References
*****************

When authoring documentation files each page (at minimum) should have a reference on its top title.
This should take the form ``dkist:<section>:<page>``, so for the index page of the ``topic_guides/`` folder it is ``dkist:topic-guides:index``.
All references should take this three element format, so a subheading in a page would be ``dkist:section:subheading``.

Testing
-------

Testing with arbitrary datasets
*******************************

The DKIST Python tools allow the test suite to run on user-provided datasets.
To enable this there are two pytest command line optionsa available, `--ds` and `--tiled-ds`.
Each takes a string parseable by `load_dataset()`.
Tests with the `accept_cli_dataset` or `accept_tiled_dataset` markers will take the value given for `--ds` or `--tiled-ds` respectively, load that dataset and pass it into the test in place of a fixture.
To only run tests using the supplied datasets you can run pytest with `-m accept_cli_dataset` and/or `-m accept_cli_tiled_dataset`.
By default the first fixture specified in the test definition is the one replaced, but if a fixture name is given to the marker that fixture will be replaced instead.

For example:

.. code-block:: python

   @pytest.mark.accept_cli_dataset("another_dataset")
   def test_something(dataset, another_dataset):
       ...

would usually run with the fixtures `dataset` and `another_dataset` as its inputs, but running `pytest --ds /path/to/dataset/ABCDE/` would run the test using the `dataset` fixture and the local dataset `ABCDE` instead.
