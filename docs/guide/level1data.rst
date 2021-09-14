.. _level1data:

Level One DKIST Data
====================

The level one data provided by the DKIST data center has been calibrated to remove any effects introduced by the telescope or instruments.
The result of these calibration recipes is a level one "dataset" which are the smallest units of DKIST data which are searchable from the data center.

Many FITS, one ASDF
-------------------

Due to the potential size of each of these datasets, and to eliminate on demand processing at the data center a single level one dataset is distributed across many FITS files. Each individual FITS file represents what can be considered to be a "single calibrated exposure".
This means that when all the processing steps have been taken into account there can be many actual exposures of the instrument involved, but these have all been reduced to a single array.
The exact contents of each FITS file vary depending on the type of instrument and the mode it was operating in, but some examples would be:

* A single wideband image without polrimetric information with a single timestamp (VBI).
* A single slit position, at one Stokes profile, with a single timestamp (ViSP / CryoNIRSP).
* A single narrow band image, at one Stokes profile, with a single timestamp (VTF).

The FITS files provided at level one by the data center, will conform to the FITS 4 specification and contain all the information about their individual array as well as DKIST specific keys in the header which specify its position in the larger dataset.
To increase the usability of these data, in addition to all the FITS files (which could number many thousands) a single metadata only ASDF file is generated per dataset.

The ASDF file provides the following information about the dataset:

* A table of all the FITS headers for all the FITS files contained in the dataset.
* An ordered nested list of the filenames of all the FITS files, providing the information about how to reconstruct the full dataset array from all the component FITS arrays.
* Information about the dtype, shape and HDU number of the arrays in the FITS file.
* A `gWCS <https://gwcs.readthedocs.io/>`__ object providing the coordinate information for the reconstructed dataset array.

These components are used by the `dkist` package to construct the `dkist.Dataset` class and it's associated `dkist.io.FileManager` class which manages the references to all the FITS files.
