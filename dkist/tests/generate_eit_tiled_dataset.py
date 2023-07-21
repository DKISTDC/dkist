#!/usr/bin/env python3
import tempfile

import numpy as np
from dkist_data_simulator.spec214.vbi import MosaicedVBIBlueDataset

import astropy
import astropy.units as u

from dkist.data.test import rootdir
from dkist_inventory.asdf_generator import dataset_from_fits


class DemoMosaicedVBIBlueDataset(MosaicedVBIBlueDataset):
    @property
    def data(self):
        return np.zeros(self.array_shape) + (self.mosaic_keys("MINDEX1") * self.mosaic_keys("MINDEX2"))

# Need this so that astropy doesn't try to download data and kill the tests
astropy.utils.iers.conf.auto_download = False
astropy.utils.iers.conf.iers_degraded_accuracy = 'ignore'

mosaic = MosaicedVBIBlueDataset(2, 1, linewave=500*u.nm, detector_shape=(2, 2))

with tempfile.TemporaryDirectory() as tempdir:
    mosaic.generate_files(tempdir, required_only=True)

    asdf_filename = rootdir / "test_tiled_dataset.asdf"
    ds = dataset_from_fits(tempdir, asdf_filename)
    print(ds)
