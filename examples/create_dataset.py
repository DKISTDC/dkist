"""
Loading a Dataset
=================

This example demonstrates the `dkist.Dataset` class.
"""

import dkist.dataset
from dkist.data.sample import EIT_DATASET

###############################################################################
# Dataset objects are created from a directory containing one asdf file and
# many FITS files. Here we use a test dataset made from EIT images.
ds = dkist.dataset.Dataset.from_directory(EIT_DATASET)

###############################################################################
# The dataset comprises of a `dask.Array` object and a `gwcs.WCS` object. The
# array object acts like a numpy array, but loads the data from the FITS files
# on demand. Creating the dataset loads no FITS files.
print(ds)
